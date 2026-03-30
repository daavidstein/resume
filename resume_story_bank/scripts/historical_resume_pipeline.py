#!/usr/bin/env python3
"""Helpers for Phase 2 historical resume ingestion and reuse-first bullet generation."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from rag_retrieval import (
    Story,
    build_jd_chunks,
    build_story_chunks,
    create_embedding_backend,
    lexical_overlap_score,
    parse_master_story_bank,
    rank_stories_for_jd,
)
from tailor_resume_model import (
    _load_jd_content,
    _parse_experience,
    _parse_jd_text,
    _parse_jd_url,
    _parse_summary_and_highlights,
)


DATE_LINE_PATTERN = re.compile(
    r"^(?:[A-Z][a-z]{2,9}\s+\d{4}|\d{4})(?:\s*[-–]\s*(?:[A-Z][a-z]{2,9}\s+\d{4}|\d{4}|Present|Current|Now))*$"
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dumps_pretty(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def load_story_bank(path: Path) -> list[Story]:
    return parse_master_story_bank(path.read_text(encoding="utf-8"))


def collect_resume_paths(resume_paths: list[str], resume_dir: str | None) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for raw in resume_paths:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"Resume input not found: {path}")
        if path not in seen:
            out.append(path)
            seen.add(path)
    if resume_dir:
        root = Path(resume_dir).expanduser().resolve()
        if not root.exists():
            raise ValueError(f"Resume directory not found: {root}")
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".md", ".txt", ".pdf"}:
                continue
            if path not in seen:
                out.append(path)
                seen.add(path)
    return out


def load_resume_source(path: Path) -> tuple[dict, str]:
    suffix = path.suffix.lower()
    warnings: list[str] = []
    if suffix not in {".md", ".txt", ".pdf"}:
        raise ValueError(f"Unsupported resume format '{suffix}' for {path}")

    if suffix in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8")
        return (
            {
                "path": str(path),
                "file_type": suffix.lstrip("."),
                "page_count": None,
                "ingest_method": "direct_text",
                "ingest_warnings": warnings,
            },
            text,
        )

    pdftotext = _which_command("pdftotext")
    if not pdftotext:
        raise ValueError(
            f"pdftotext is required to ingest PDF resumes: {path}"
        )
    try:
        result = subprocess.run(
            [pdftotext, str(path), "-"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ValueError(f"Unable to execute pdftotext for {path}: {exc}") from exc
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown pdftotext failure"
        raise ValueError(f"pdftotext failed for {path}: {stderr}")

    page_count = _pdf_page_count(path)
    if page_count is None:
        warnings.append("Unable to determine PDF page count via pdfinfo")

    normalized = normalize_pdf_text(result.stdout)
    if not normalized.strip():
        raise ValueError(
            f"PDF text extraction produced no usable text for {path}; scanned/image-only PDFs are unsupported in Phase 2"
        )

    return (
        {
            "path": str(path),
            "file_type": "pdf",
            "page_count": page_count,
            "ingest_method": "pdftotext",
            "ingest_warnings": warnings,
        },
        normalized,
    )


def extract_historical_bullet_inventory(paths: list[Path]) -> dict:
    source_resumes: list[dict] = []
    bullets: list[dict] = []
    counter = 1
    for path in paths:
        try:
            source_meta, text = load_resume_source(path)
        except ValueError as exc:
            source_resumes.append(
                {
                    "path": str(path),
                    "file_type": path.suffix.lower().lstrip("."),
                    "page_count": None,
                    "ingest_method": "failed",
                    "ingest_warnings": [str(exc)],
                }
            )
            continue
        source_resumes.append(source_meta)
        extracted = extract_resume_bullets(
            text=text,
            resume_path=str(path),
            file_type=source_meta["file_type"],
        )
        for item in extracted:
            item["historical_bullet_id"] = f"HB-{counter:03d}"
            counter += 1
            bullets.append(item)
    return {
        "artifact_type": "historical_bullet_inventory",
        "generated_at": utc_timestamp(),
        "source_resumes": source_resumes,
        "bullets": bullets,
    }


def extract_resume_bullets(text: str, resume_path: str, file_type: str) -> list[dict]:
    if file_type in {"md", "txt"} and "## Professional Experience" in text:
        return _extract_markdown_resume_bullets(text, resume_path)
    return _extract_generic_resume_bullets(text, resume_path)


def _extract_markdown_resume_bullets(text: str, resume_path: str) -> list[dict]:
    bullets: list[dict] = []
    about_sentences, highlights = _parse_summary_and_highlights(text)
    for sentence in about_sentences:
        cleaned = normalize_bullet_text(sentence)
        if cleaned:
            bullets.append(
                _new_historical_bullet(
                    resume_path=resume_path,
                    section="summary",
                    text=cleaned,
                )
            )
    for bullet in highlights:
        cleaned = normalize_bullet_text(bullet)
        if cleaned:
            bullets.append(
                _new_historical_bullet(
                    resume_path=resume_path,
                    section="summary",
                    text=cleaned,
                )
            )

    for role in _parse_experience(text):
        role_skills = ""
        for bullet in role["bullets"]:
            cleaned = normalize_bullet_text(bullet)
            if not cleaned:
                continue
            if cleaned.lower().startswith("skills/tools:"):
                role_skills = cleaned.split(":", 1)[1].strip()
                continue
            bullets.append(
                _new_historical_bullet(
                    resume_path=resume_path,
                    section="experience",
                    role_title=role["title"],
                    role_org=role["company"],
                    text=cleaned,
                    skills_tools_line=role_skills,
                )
            )
    return bullets


def _extract_generic_resume_bullets(text: str, resume_path: str) -> list[dict]:
    bullets: list[dict] = []
    lines = _prepare_generic_lines(text)
    current_section = "other"
    current_role_title = ""
    current_role_org = ""
    current_skills = ""
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        lower = line.lower()
        if lower in {"summary", "about me", "relevant experience highlights"}:
            current_section = "summary"
            idx += 1
            continue
        if lower in {"experience", "professional experience"}:
            current_section = "experience"
            idx += 1
            continue
        if lower == "skills":
            current_section = "skills"
            current_role_title = ""
            current_role_org = ""
            current_skills = ""
            idx += 1
            continue

        next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
        if current_section == "experience" and " | " in line and not line.startswith("- "):
            if DATE_LINE_PATTERN.match(next_line):
                current_role_title, current_role_org = _parse_role_header(line)
                current_skills = ""
                idx += 2
                continue
            if DATE_LINE_PATTERN.search(line):
                current_role_title, current_role_org = _parse_role_header(line)
                current_skills = ""
                idx += 1
                continue

        if line.startswith("- "):
            cleaned = normalize_bullet_text(line[2:])
            if not cleaned:
                idx += 1
                continue
            if cleaned.lower().startswith("skills/tools:"):
                current_skills = cleaned.split(":", 1)[1].strip()
                idx += 1
                continue
            bullets.append(
                _new_historical_bullet(
                    resume_path=resume_path,
                    section=current_section,
                    role_title=current_role_title,
                    role_org=current_role_org,
                    text=cleaned,
                    skills_tools_line=current_skills,
                )
            )
        idx += 1
    return bullets


def _prepare_generic_lines(text: str) -> list[str]:
    raw_lines = normalize_pdf_text(text).splitlines()
    return [line.strip() for line in raw_lines if line.strip()]


def normalize_pdf_text(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned_lines: list[str] = []
    current = ""
    for raw in lines:
        normalized = raw.replace("\x0c", " ").replace("•", "- ").strip()
        if not normalized:
            if current:
                cleaned_lines.append(current.strip())
                current = ""
            continue
        normalized = re.sub(r"^[•●▪◦]\s*", "- ", normalized)
        normalized = re.sub(r"-\s+", "- ", normalized)
        if normalized.isdigit():
            continue
        if _starts_structural_line(normalized):
            if current:
                cleaned_lines.append(current.strip())
            current = normalized
            continue
        if current:
            current = f"{current} {normalized}"
        else:
            current = normalized
    if current:
        cleaned_lines.append(current.strip())
    return "\n".join(cleaned_lines)


def normalize_bullet_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = cleaned.strip("•").strip()
    return cleaned


def render_historical_inventory_markdown(data: dict) -> str:
    lines = ["# Historical Bullet Inventory", ""]
    lines.append(f"Generated at: `{data['generated_at']}`")
    lines.append("")
    lines.append("## Source Resumes")
    for source in data.get("source_resumes", []):
        page_count = source.get("page_count")
        page_label = page_count if page_count is not None else "unknown"
        lines.append(
            f"- `{source['path']}` ({source['file_type']}, method={source['ingest_method']}, pages={page_label})"
        )
        for warning in source.get("ingest_warnings", []):
            lines.append(f"  warning: {warning}")
    lines.append("")
    lines.append("## Extracted Bullets")
    for bullet in data.get("bullets", []):
        lines.append(f"### {bullet['historical_bullet_id']}")
        lines.append(f"- section: `{bullet['section']}`")
        if bullet.get("role_title"):
            lines.append(f"- role_title: `{bullet['role_title']}`")
        if bullet.get("role_org"):
            lines.append(f"- role_org: `{bullet['role_org']}`")
        if bullet.get("skills_tools_line"):
            lines.append(f"- skills_tools_line: `{bullet['skills_tools_line']}`")
        lines.append(f"- text: {bullet['text']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def link_historical_bullets(inventory: dict, stories: list[Story], top_k: int = 3) -> dict:
    backend = create_embedding_backend("local_hash_v1")
    story_vectors = {story.story_id: backend.embed(story.full_text) for story in stories}
    linked = json.loads(json.dumps(inventory))
    linked["artifact_type"] = "linked_historical_bullet_inventory"
    linked["generated_at"] = utc_timestamp()

    for bullet in linked.get("bullets", []):
        text = bullet.get("text", "")
        bullet_vec = backend.embed(text)
        candidates: list[dict] = []
        for story in stories:
            lexical = lexical_overlap_score(text, story.full_text)
            semantic = 0.0
            if bullet_vec and story_vectors[story.story_id]:
                from rag_retrieval import cosine_sparse

                semantic = cosine_sparse(bullet_vec, story_vectors[story.story_id])
            score = (0.65 * semantic) + (0.35 * lexical)
            if score <= 0:
                continue
            candidates.append(
                {
                    "story_id": story.story_id,
                    "story_title": story.title,
                    "score": round(score, 6),
                    "semantic_similarity": round(semantic, 6),
                    "lexical_overlap": round(lexical, 6),
                }
            )
        candidates.sort(key=lambda item: item["score"], reverse=True)
        candidates = candidates[:top_k]
        bullet["candidate_story_links"] = candidates
        if not candidates:
            bullet["linked_story_ids"] = []
            bullet["link_confidence"] = "unlinked"
            bullet["link_method"] = ""
            continue
        top = candidates[0]
        second_score = candidates[1]["score"] if len(candidates) > 1 else 0.0
        confidence = _link_confidence(top["score"], second_score)
        bullet["link_confidence"] = confidence
        bullet["link_method"] = "heuristic_similarity"
        bullet["linked_story_ids"] = [top["story_id"]] if confidence != "unlinked" else []
    return linked


def render_linked_inventory_markdown(data: dict) -> str:
    lines = ["# Linked Historical Bullet Inventory", ""]
    lines.append(f"Generated at: `{data['generated_at']}`")
    lines.append("")
    for bullet in data.get("bullets", []):
        lines.append(f"## {bullet['historical_bullet_id']}")
        lines.append(f"- text: {bullet['text']}")
        lines.append(f"- link_confidence: `{bullet.get('link_confidence', 'unlinked')}`")
        if bullet.get("linked_story_ids"):
            lines.append(f"- linked_story_ids: `{', '.join(bullet['linked_story_ids'])}`")
        for candidate in bullet.get("candidate_story_links", []):
            lines.append(
                "- candidate: "
                f"`{candidate['story_id']}` score={candidate['score']} lexical={candidate['lexical_overlap']} semantic={candidate['semantic_similarity']}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_story_coverage_report(linked_inventory: dict, stories: list[Story]) -> dict:
    bullets = linked_inventory.get("bullets", [])
    report_rows = []
    for story in stories:
        matching = [
            bullet for bullet in bullets if story.story_id in bullet.get("linked_story_ids", [])
        ]
        if any(bullet.get("link_confidence") == "strong" for bullet in matching):
            coverage_status = "well_represented"
        elif matching:
            coverage_status = "partially_represented"
        else:
            coverage_status = "not_represented"
        report_rows.append(
            {
                "story_id": story.story_id,
                "story_title": story.title,
                "coverage_status": coverage_status,
                "linked_historical_bullet_ids": [bullet["historical_bullet_id"] for bullet in matching],
                "representative_linked_bullets": [bullet["text"] for bullet in matching[:2]],
            }
        )
    return {
        "artifact_type": "story_coverage_report",
        "generated_at": utc_timestamp(),
        "stories": report_rows,
    }


def render_story_coverage_markdown(data: dict) -> str:
    lines = ["# Story Coverage Report", ""]
    lines.append(f"Generated at: `{data['generated_at']}`")
    lines.append("")
    for row in data.get("stories", []):
        lines.append(f"## {row['story_id']} - {row['story_title']}")
        lines.append(f"- coverage_status: `{row['coverage_status']}`")
        if row.get("linked_historical_bullet_ids"):
            lines.append(
                f"- linked_historical_bullet_ids: `{', '.join(row['linked_historical_bullet_ids'])}`"
            )
        for bullet in row.get("representative_linked_bullets", []):
            lines.append(f"- example: {bullet}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_candidate_bullet_batch(
    linked_inventory: dict,
    stories: list[Story],
    *,
    jd_text: str = "",
    job_context: dict | None = None,
    selected_story_ids: set[str] | None = None,
) -> dict:
    story_map = {story.story_id: story for story in stories}
    target_story_ids = list(story_map.keys())
    if selected_story_ids:
        target_story_ids = [story_id for story_id in target_story_ids if story_id in selected_story_ids]
    elif jd_text.strip():
        backend = create_embedding_backend("local_hash_v1")
        story_chunks = build_story_chunks(stories)
        ranked = rank_stories_for_jd(
            build_jd_chunks(jd_text),
            stories,
            story_chunks,
            backend,
            cache=None,
            top_k_per_jd_chunk=3,
        )
        ranked_ids = [row["story_id"] for row in ranked if row["score"] > 0]
        if ranked_ids:
            target_story_ids = ranked_ids[: min(len(ranked_ids), 10)]

    bullets: list[dict] = []
    counter = 1
    for story_id in target_story_ids:
        story = story_map[story_id]
        linked = [
            item
            for item in linked_inventory.get("bullets", [])
            if story_id in item.get("linked_story_ids", [])
        ]
        linked.sort(key=lambda item: _confidence_rank(item.get("link_confidence", "unlinked")), reverse=True)
        if linked and linked[0].get("link_confidence") == "strong":
            best = linked[0]
            text = normalize_bullet_text(best["text"])
            origin_mode = "historical_reuse"
            source_historical_ids = [best["historical_bullet_id"]]
            coverage_reason = "well_represented"
        elif linked:
            best = linked[0]
            text = adapt_historical_bullet(best["text"], story, jd_text)
            origin_mode = "historical_adaptation"
            source_historical_ids = [best["historical_bullet_id"]]
            coverage_reason = "partial_gap"
        else:
            text = synthesize_story_bullet(story, jd_text)
            origin_mode = "story_synthesis"
            source_historical_ids = []
            coverage_reason = "uncovered_story"

        if not text.strip():
            continue
        bullets.append(
            {
                "candidate_bullet_id": f"CB-{counter:03d}",
                "text": text,
                "source_story_ids": [story.story_id],
                "source_historical_bullet_ids": source_historical_ids,
                "origin_mode": origin_mode,
                "generation_path": "reuse_first_v1",
                "coverage_reason": coverage_reason,
                "guardrail_notes": extract_guardrail_notes(story),
                "review": {"label": "", "notes": ""},
            }
        )
        counter += 1

    deduped: list[dict] = []
    seen_texts: set[str] = set()
    for bullet in bullets:
        key = bullet["text"].strip().lower()
        if key in seen_texts:
            continue
        seen_texts.add(key)
        deduped.append(bullet)

    return {
        "artifact_type": "candidate_bullet_batch",
        "generated_at": utc_timestamp(),
        "generation_mode": "reuse_first_v1",
        "job_context": job_context or {},
        "bullets": deduped,
    }


def render_candidate_bullets_markdown(data: dict, stories: list[Story]) -> str:
    story_map = {story.story_id: story.title for story in stories}
    lines = ["# Candidate Bullet Batch", ""]
    lines.append(f"Generated at: `{data['generated_at']}`")
    lines.append(f"Generation mode: `{data['generation_mode']}`")
    job_context = data.get("job_context", {})
    if job_context.get("job_description_path"):
        lines.append(f"Job description: `{job_context['job_description_path']}`")
    if job_context.get("job_description_url"):
        lines.append(f"Job description URL: `{job_context['job_description_url']}`")
    if job_context.get("jd_excerpt"):
        lines.append("")
        lines.append("## JD Excerpt")
        lines.append(job_context["jd_excerpt"])
    lines.append("")
    for bullet in data.get("bullets", []):
        lines.append(f"## {bullet['candidate_bullet_id']}")
        lines.append(f"- text: {bullet['text']}")
        lines.append(f"- origin_mode: `{bullet['origin_mode']}`")
        lines.append(f"- coverage_reason: `{bullet['coverage_reason']}`")
        story_ids = bullet.get("source_story_ids", [])
        if story_ids:
            lines.append(f"- source_story_ids: `{', '.join(story_ids)}`")
            for story_id in story_ids:
                title = story_map.get(story_id, "")
                if title:
                    lines.append(f"  story_title: `{story_id}` -> {title}")
        historical_ids = bullet.get("source_historical_bullet_ids", [])
        if historical_ids:
            lines.append(f"- source_historical_bullet_ids: `{', '.join(historical_ids)}`")
        guardrails = bullet.get("guardrail_notes", {})
        if guardrails:
            lines.append(f"- rewrite_safety: `{guardrails.get('rewrite_safety', '')}`")
            for field in ("wording_constraints", "caveats", "forbidden_claims"):
                values = guardrails.get(field) or []
                lines.append(f"- {field}: `{', '.join(values)}`")
        lines.append("- Review Label:")
        lines.append("- Review Notes:")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_output_bundle(data: dict, output: Path, fmt: str, markdown_renderer) -> list[Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if fmt in {"json", "both"}:
        json_path = output if output.suffix.lower() == ".json" else output.with_suffix(".json")
        json_path.write_text(dumps_pretty(data), encoding="utf-8")
        written.append(json_path)
    if fmt in {"markdown", "both"}:
        md_path = output if output.suffix.lower() == ".md" else output.with_suffix(".md")
        md_path.write_text(markdown_renderer(data), encoding="utf-8")
        written.append(md_path)
    return written


def write_output_bundle_with_story_context(
    data: dict,
    output: Path,
    fmt: str,
    markdown_renderer,
    stories: list[Story],
) -> list[Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if fmt in {"json", "both"}:
        json_path = output if output.suffix.lower() == ".json" else output.with_suffix(".json")
        json_path.write_text(dumps_pretty(data), encoding="utf-8")
        written.append(json_path)
    if fmt in {"markdown", "both"}:
        md_path = output if output.suffix.lower() == ".md" else output.with_suffix(".md")
        md_path.write_text(markdown_renderer(data, stories), encoding="utf-8")
        written.append(md_path)
    return written


def load_json_artifact(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_job_context(job_description: str | None, job_description_url: str | None) -> tuple[str, dict]:
    if job_description and job_description_url:
        raise ValueError("Use either --job-description or --job-description-url, not both")
    if job_description:
        path = Path(job_description).expanduser()
        text, requirements = _load_jd_content(path)
        keywords, _reqs = _parse_jd_text(text, requirements=requirements)
        return text, {
            "job_description_path": str(path),
            "job_description_url": "",
            "jd_excerpt": text[:500],
            "jd_keywords": sorted(keywords),
        }
    if job_description_url:
        keywords, requirements, _artifact = _parse_jd_url(job_description_url)
        excerpt = "\n".join(requirements[:6])[:500]
        return excerpt, {
            "job_description_path": "",
            "job_description_url": job_description_url,
            "jd_excerpt": excerpt,
            "jd_keywords": sorted(keywords),
        }
    return "", {}


def extract_guardrail_notes(story: Story) -> dict:
    metadata = story.structured_metadata or {}
    return {
        "rewrite_safety": metadata.get("rewrite_safety", ""),
        "wording_constraints": list(metadata.get("wording_constraints", [])) if isinstance(metadata.get("wording_constraints", []), list) else [],
        "caveats": list(metadata.get("caveats", [])) if isinstance(metadata.get("caveats", []), list) else [],
        "forbidden_claims": list(metadata.get("forbidden_claims", [])) if isinstance(metadata.get("forbidden_claims", []), list) else [],
    }


def adapt_historical_bullet(text: str, story: Story, jd_text: str) -> str:
    base = normalize_bullet_text(text).rstrip(".")
    outcome = _best_story_fragment(story.outcomes, jd_text)
    if outcome and lexical_overlap_score(base, outcome) < 0.3:
        return f"{base}; {outcome[0].lower() + outcome[1:]}" if outcome else base
    return base


def synthesize_story_bullet(story: Story, jd_text: str) -> str:
    action = _best_story_fragment(story.actions, jd_text)
    outcome = _best_story_fragment(story.outcomes, jd_text)
    if action and outcome:
        return f"{action.rstrip('.')}; {outcome[0].lower() + outcome[1:]}"
    if action:
        return action
    if outcome:
        return outcome
    return story.title


def _best_story_fragment(text: str, jd_text: str) -> str:
    candidates = [line.strip()[2:].strip() for line in text.splitlines() if line.strip().startswith("- ")]
    if not candidates:
        candidates = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if not candidates:
        return ""
    if not jd_text.strip():
        return candidates[0]
    scored = sorted(
        candidates,
        key=lambda item: lexical_overlap_score(item, jd_text),
        reverse=True,
    )
    return scored[0]


def _new_historical_bullet(
    *,
    resume_path: str,
    section: str,
    text: str,
    role_title: str = "",
    role_org: str = "",
    skills_tools_line: str = "",
) -> dict:
    return {
        "historical_bullet_id": "",
        "resume_path": resume_path,
        "section": section,
        "role_title": role_title,
        "role_org": role_org,
        "text": text,
        "skills_tools_line": skills_tools_line,
        "linked_story_ids": [],
        "candidate_story_links": [],
        "link_confidence": "unlinked",
        "link_method": "",
        "review_notes": "",
    }


def _parse_role_header(line: str) -> tuple[str, str]:
    parts = [part.strip() for part in line.split("|")]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return line.strip(), ""


def _starts_structural_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    lower = stripped.lower()
    if stripped.startswith("- "):
        return True
    if lower in {"summary", "experience", "skills", "professional experience", "about me", "relevant experience highlights"}:
        return True
    if " | " in stripped:
        return True
    if DATE_LINE_PATTERN.match(stripped):
        return True
    return False


def _pdf_page_count(path: Path) -> int | None:
    pdfinfo = _which_command("pdfinfo")
    if not pdfinfo:
        return None
    result = subprocess.run(
        [pdfinfo, str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    if not match:
        return None
    return int(match.group(1))


def _which_command(name: str) -> str | None:
    from shutil import which

    return which(name)


def _link_confidence(top_score: float, second_score: float) -> str:
    if top_score < 0.08:
        return "unlinked"
    if top_score >= 0.25 and (top_score - second_score) >= 0.06:
        return "strong"
    if top_score >= 0.14:
        return "partial"
    return "weak"


def _confidence_rank(value: str) -> int:
    mapping = {"strong": 3, "partial": 2, "weak": 1, "unlinked": 0}
    return mapping.get(value, 0)
