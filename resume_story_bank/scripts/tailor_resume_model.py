#!/usr/bin/env python3
"""Generate a resume model JSON from base resume + job description markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from validate_resume_model import BUDGET_LIMITS, validate_model


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
    "you",
    "your",
}

STORY_ID_PATTERN = re.compile(r"^SB-\d{3,}$")


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^## .+$", text[start:], re.MULTILINE)
    if not next_heading:
        return text[start:].strip()
    return text[start : start + next_heading.start()].strip()


def _tokens(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-zA-Z][a-zA-Z0-9+#/.-]*", text.lower())
        if len(tok) > 2 and tok not in STOPWORDS
    }


def _score(text: str, keywords: set[str]) -> int:
    return len(_tokens(text) & keywords)


def _parse_basics(text: str, default_location: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = ""
    if lines and lines[0].startswith("# "):
        name = lines[0][2:].strip()
    contact = lines[1] if len(lines) > 1 else ""

    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", contact)
    phone_match = re.search(r"(\+?\d[\d\-\s().]{7,}\d)", contact)
    url_matches = re.findall(r"`([^`]+)`", contact)
    if not url_matches:
        url_matches = re.findall(r"\b(?:https?://)?(?:github\.com|linkedin\.com)/[^\s|]+", contact)

    links: list[dict] = []
    for url in url_matches:
        normalized = url if url.startswith("http") else f"https://{url}"
        label = "Link"
        if "github.com" in url.lower():
            label = "GitHub"
        elif "linkedin.com" in url.lower():
            label = "LinkedIn"
        links.append({"label": label, "url": normalized})

    return {
        "name": name or "Unknown Candidate",
        "email": email_match.group(0) if email_match else "unknown@example.com",
        "phone": phone_match.group(0) if phone_match else "Unknown",
        "location": default_location,
        "links": links,
    }


def _parse_summary_and_highlights(text: str) -> tuple[list[str], list[str]]:
    about_text = _section(text, "About Me")
    about_sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", about_text) if part.strip()]

    highlights = []
    highlights_block = _section(text, "Relevant Experience Highlights")
    for line in highlights_block.splitlines():
        cleaned = line.strip()
        if cleaned.startswith("- "):
            highlights.append(cleaned[2:].strip())
    return about_sentences, highlights


def _parse_experience(text: str) -> list[dict]:
    block = _section(text, "Professional Experience")
    if not block:
        return []

    roles: list[dict] = []
    chunks = re.split(r"(?m)^### ", block)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = [line.rstrip() for line in chunk.splitlines()]
        title = lines[0].strip()
        meta_line = ""
        for line in lines[1:]:
            if line.strip():
                meta_line = line.strip()
                break

        company = "Unknown Company"
        start_date = "Unknown"
        end_date = "Unknown"
        if "|" in meta_line:
            company = meta_line.split("|", 1)[0].strip()
            date_part = meta_line.split("|", 1)[1].strip()
            if " - " in date_part:
                start_date, end_date = [part.strip() for part in date_part.split(" - ", 1)]
            elif "-" in date_part:
                start_date, end_date = [part.strip() for part in date_part.split("-", 1)]
            else:
                start_date = date_part
        bullets = [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ")]
        roles.append(
            {
                "title": title,
                "company": company,
                "start_date": start_date,
                "end_date": end_date,
                "bullets": bullets,
            }
        )
    return roles


def _preflight_base_resume(text: str) -> list[str]:
    errors: list[str] = []
    required_headings = [
        "About Me",
        "Professional Experience",
    ]
    for heading in required_headings:
        if not _section(text, heading):
            errors.append(f"Missing required base-resume section: '## {heading}'")

    experience = _parse_experience(text)
    if not experience:
        errors.append("No roles found under '## Professional Experience' (expected '### <Role>' entries)")
    else:
        for idx, role in enumerate(experience):
            if not role["bullets"]:
                errors.append(
                    f"Role index {idx} ('{role['title']}') has no bullets; expected '- ' bullet lines"
                )
    return errors


def _parse_education(text: str) -> list[dict]:
    block = _section(text, "Education")
    out = []
    for line in block.splitlines():
        cleaned = line.strip()
        if not cleaned.startswith("- "):
            continue
        body = cleaned[2:].strip()
        degree = body
        institution = "Unknown Institution"
        if "," in body:
            degree_part, rem = body.split(",", 1)
            degree = degree_part.strip()
            institution = rem.split("|", 1)[0].strip()
        out.append({"institution": institution, "degree": degree})
    return out


def _parse_skills(experience: list[dict], highlights: list[str]) -> dict:
    skills: set[str] = set()
    skill_prefix = "skills/tools:"
    for role in experience:
        for bullet in role["bullets"]:
            lower = bullet.lower()
            if lower.startswith(skill_prefix):
                body = bullet[len(skill_prefix) :].strip()
                for part in body.split(","):
                    skill = part.strip().rstrip(".")
                    if skill:
                        skills.add(skill)
    for hl in highlights:
        for term in re.findall(r"\b(PyTorch|Python|SQL|AWS|MLOps|CI/CD|HDBSCAN|UMAP|LLM|NLP)\b", hl, re.IGNORECASE):
            skills.add(term)
    return {"groups": [{"name": "Core Skills", "items": sorted(skills)}] if skills else [{"name": "Core Skills", "items": ["Python"]}]}


def _parse_story_bank(path: Path, default_story_id: str) -> list[tuple[str, str]]:
    if not path.exists():
        return [(default_story_id, "")]
    text = path.read_text(encoding="utf-8")
    blocks: list[tuple[str, str]] = []
    for match in re.finditer(r"(?ms)^## Story:.*?(?=^## Story:|\Z)", text):
        block = match.group(0)
        id_match = re.search(r"(?m)^### Story ID\s*$\n+([^\n]+)\s*$", block)
        if not id_match:
            continue
        story_id = id_match.group(1).strip()
        if STORY_ID_PATTERN.match(story_id):
            blocks.append((story_id, block))
    if not blocks:
        return [(default_story_id, "")]
    return blocks


def _best_story_ids(text: str, story_blocks: list[tuple[str, str]]) -> list[str]:
    query = _tokens(text)
    if not query:
        return [story_blocks[0][0]]
    scored = []
    for story_id, block in story_blocks:
        scored.append((len(query & _tokens(block)), story_id))
    scored.sort(reverse=True)
    top_score = scored[0][0]
    if top_score <= 0:
        return [scored[0][1]]
    return [sid for score, sid in scored[:2] if score == top_score or score > 0][:2]


def _parse_jd(path: Path) -> tuple[set[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    requirements = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned.startswith("- "):
            requirements.append(cleaned[2:].strip())
    if not requirements:
        requirements = [part.strip() for part in re.split(r"[.\n]", text) if part.strip()]
    return _tokens(text), requirements


def build_model(
    base_resume_text: str,
    jd_keywords: set[str],
    jd_requirements: list[str],
    page_budget: int,
    default_location: str,
    story_blocks: list[tuple[str, str]],
) -> dict:
    limits = BUDGET_LIMITS[page_budget]
    basics = _parse_basics(base_resume_text, default_location=default_location)
    about_sentences, highlights = _parse_summary_and_highlights(base_resume_text)
    experience_raw = _parse_experience(base_resume_text)
    education = _parse_education(base_resume_text)
    skills = _parse_skills(experience_raw, highlights)

    summary_candidates = about_sentences + highlights
    summary_scored = sorted(summary_candidates, key=lambda s: (_score(s, jd_keywords), len(s)), reverse=True)
    summary_text = summary_scored[: limits["summary_bullets_max"]]
    summary = [{"bullet_id": f"SUM-{idx:03d}", "text": text} for idx, text in enumerate(summary_text, start=1)]

    role_entries = []
    for role in experience_raw:
        role_score = _score(role["title"] + " " + role["company"], jd_keywords) + sum(
            _score(bullet, jd_keywords) for bullet in role["bullets"]
        )
        bullet_pairs = sorted(
            role["bullets"],
            key=lambda bullet: (_score(bullet, jd_keywords), len(bullet)),
            reverse=True,
        )
        bullets = bullet_pairs[: limits["experience_bullets_per_role_max"]]
        role_entries.append((role_score, role, bullets))

    role_entries.sort(key=lambda item: item[0], reverse=True)
    selected_role_entries = role_entries[: limits["experience_roles_max"]]
    selected_role_set = {id(item[1]) for item in selected_role_entries}
    selected_role_entries.sort(key=lambda item: next(idx for idx, r in enumerate(experience_raw) if id(r) == id(item[1])))

    experience = []
    traceability = []
    exp_counter = 1
    for _, role, bullets in selected_role_entries:
        role_bullets = []
        for bullet in bullets:
            bullet_id = f"EXP-{exp_counter:03d}"
            exp_counter += 1
            role_bullets.append({"bullet_id": bullet_id, "text": bullet})
            traceability.append({"bullet_id": bullet_id, "story_ids": _best_story_ids(bullet, story_blocks)})
        experience.append(
            {
                "title": role["title"],
                "company": role["company"],
                "start_date": role["start_date"],
                "end_date": role["end_date"],
                "bullets": role_bullets,
            }
        )

    for item in summary:
        traceability.append({"bullet_id": item["bullet_id"], "story_ids": _best_story_ids(item["text"], story_blocks)})

    selected_text = " ".join(
        [item["text"] for item in summary]
        + [bullet["text"] for role in experience for bullet in role["bullets"]]
    )
    selected_tokens = _tokens(selected_text)
    gaps = []
    for req in jd_requirements:
        if _tokens(req) and not (_tokens(req) & selected_tokens):
            gaps.append(f"Potential gap: {req}")
    gaps = gaps[:3]

    return {
        "page_budget": page_budget,
        "basics": basics,
        "summary": summary,
        "experience": experience,
        "skills": skills,
        "education": education,
        "gaps": gaps,
        "traceability": traceability,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Tailor a resume model from base resume + JD markdown.")
    parser.add_argument("--base-resume", required=True, help="Path to base resume markdown.")
    parser.add_argument("--job-description", required=True, help="Path to job description markdown.")
    parser.add_argument(
        "--master-story-bank",
        default="data/processed/master_story_bank.md",
        help="Path to master story bank markdown.",
    )
    parser.add_argument("--output", required=True, help="Path to output resume model JSON.")
    parser.add_argument("--page-budget", type=int, choices=(1, 2), default=2, help="Page budget (default: 2).")
    parser.add_argument("--default-location", default="Remote", help="Fallback location for basics.")
    parser.add_argument("--default-story-id", default="SB-000", help="Fallback story ID.")
    args = parser.parse_args()

    if not STORY_ID_PATTERN.match(args.default_story_id):
        print("ERROR: --default-story-id must match SB-### format")
        return 1

    base_path = Path(args.base_resume)
    jd_path = Path(args.job_description)
    story_path = Path(args.master_story_bank)
    output_path = Path(args.output)

    if not base_path.exists():
        print(f"ERROR: base resume not found: {base_path}")
        return 1
    if not jd_path.exists():
        print(f"ERROR: job description not found: {jd_path}")
        return 1

    base_text = base_path.read_text(encoding="utf-8")
    preflight_errors = _preflight_base_resume(base_text)
    if preflight_errors:
        print("ERROR: base resume format preflight failed")
        for err in preflight_errors:
            print(f"- {err}")
        return 1

    jd_keywords, jd_requirements = _parse_jd(jd_path)
    story_blocks = _parse_story_bank(story_path, default_story_id=args.default_story_id)

    model = build_model(
        base_resume_text=base_text,
        jd_keywords=jd_keywords,
        jd_requirements=jd_requirements,
        page_budget=args.page_budget,
        default_location=args.default_location,
        story_blocks=story_blocks,
    )
    errors = validate_model(model)
    if errors:
        print("ERROR: generated model validation failed")
        for err in errors:
            print(f"- {err}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote tailored model: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
