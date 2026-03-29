#!/usr/bin/env python3
"""Generate a resume model JSON from base resume + job description input."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from rag_retrieval import (
    Chunk,
    EmbeddingCache,
    EmbeddingBackend,
    Story,
    build_jd_chunks,
    build_story_chunks,
    create_embedding_backend,
    create_selection_report,
    cosine_sparse,
    lexical_overlap_score,
    parse_master_story_bank,
    rank_stories_for_jd,
    dumps_pretty,
)
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


class _JDHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_li = False
        self._li_buffer: list[str] = []
        self.requirements: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "li":
            self._in_li = True
            self._li_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "li":
            cleaned = " ".join(part.strip() for part in self._li_buffer if part.strip()).strip()
            if cleaned:
                self.requirements.append(cleaned)
            self._li_buffer = []
            self._in_li = False

    def handle_data(self, data: str) -> None:
        unescaped = html.unescape(data)
        if self._in_li:
            self._li_buffer.append(unescaped)
        self.text_parts.append(unescaped)


def _load_jd_content(path: Path) -> tuple[str, list[str]]:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8")
        requirements = []
        for line in text.splitlines():
            cleaned = line.strip()
            if cleaned.startswith("- "):
                requirements.append(cleaned[2:].strip())
        return text, requirements

    if suffix in {".html", ".htm"}:
        parser = _JDHTMLParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
        text = "\n".join(part.strip() for part in parser.text_parts if part.strip())
        return text, parser.requirements

    raise ValueError(
        f"Unsupported JD format '{suffix}'. Supported extensions: .md, .txt, .html, .htm"
    )


def _parse_jd_text(text: str, requirements: list[str] | None = None) -> tuple[set[str], list[str]]:
    extracted = requirements[:] if requirements else []
    if not extracted:
        for line in text.splitlines():
            cleaned = line.strip()
            if cleaned.startswith("- "):
                extracted.append(cleaned[2:].strip())
    if not extracted:
        extracted = [part.strip() for part in re.split(r"[.\n]", text) if part.strip()]
    return _tokens(text), extracted


def _save_jd_fetch_artifact(
    *,
    url: str,
    raw: bytes,
    content_type: str,
    encoding: str,
    cache_dir: Path,
    is_html: bool,
) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    extension = ".html" if is_html else ".txt"
    stem = f"{timestamp}_{url_hash}"
    raw_path = cache_dir / f"{stem}{extension}"
    metadata_path = cache_dir / f"{stem}.json"

    raw_path.write_bytes(raw)
    metadata = {
        "url": url,
        "fetched_at_utc": timestamp,
        "content_type": content_type,
        "encoding": encoding,
        "is_html": is_html,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "raw_path": str(raw_path),
        "metadata_path": str(metadata_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def _parse_jd_url(
    url: str,
    jd_fetch_cache_dir: Path | None = None,
) -> tuple[set[str], list[str], dict | None]:
    request = Request(url, headers={"User-Agent": "resume-story-bank/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read()
            content_type = (response.headers.get("Content-Type") or "").lower()
            encoding = response.headers.get_content_charset() or "utf-8"
    except URLError as exc:
        raise ValueError(f"Unable to fetch job description URL: {exc}") from exc

    text = raw.decode(encoding, errors="replace")
    is_html = "html" in content_type or url.lower().endswith((".html", ".htm"))
    fetch_artifact: dict | None = None
    if jd_fetch_cache_dir:
        fetch_artifact = _save_jd_fetch_artifact(
            url=url,
            raw=raw,
            content_type=content_type,
            encoding=encoding,
            cache_dir=jd_fetch_cache_dir,
            is_html=is_html,
        )

    if is_html:
        parser = _JDHTMLParser()
        parser.feed(text)
        parser.close()
        body_text = "\n".join(part.strip() for part in parser.text_parts if part.strip())
        keywords, requirements = _parse_jd_text(body_text, requirements=parser.requirements)
        return keywords, requirements, fetch_artifact

    keywords, requirements = _parse_jd_text(text)
    return keywords, requirements, fetch_artifact


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


def _embed_text(
    text: str,
    embedding_backend: EmbeddingBackend,
    embedding_cache: EmbeddingCache | None,
) -> dict[int, float]:
    payload = text.strip()
    if not payload:
        return {}
    if embedding_cache:
        return embedding_cache.get_or_embed(payload, embedding_backend)
    return embedding_backend.embed(payload)


def _hybrid_score(
    text: str,
    jd_text: str,
    jd_vector: dict[int, float],
    embedding_backend: EmbeddingBackend,
    embedding_cache: EmbeddingCache | None,
    semantic_weight: float = 0.7,
    lexical_weight: float = 0.3,
) -> float:
    text_vec = _embed_text(text, embedding_backend, embedding_cache)
    semantic = cosine_sparse(text_vec, jd_vector) if text_vec and jd_vector else 0.0
    lexical = lexical_overlap_score(text, jd_text) if jd_text else 0.0
    return (semantic_weight * semantic) + (lexical_weight * lexical)


def _cache_reuse_summary(
    texts: list[str],
    embedding_backend: EmbeddingBackend,
    embedding_cache: EmbeddingCache | None,
) -> dict[str, int] | None:
    if not embedding_cache:
        return None
    unique_texts = []
    seen: set[str] = set()
    for text in texts:
        payload = text.strip()
        if not payload or payload in seen:
            continue
        seen.add(payload)
        unique_texts.append(payload)
    total = len(unique_texts)
    hits = sum(
        1
        for payload in unique_texts
        if EmbeddingCache._key(payload, embedding_backend.name) in embedding_cache.records
    )
    return {
        "total": total,
        "hits": hits,
        "misses": total - hits,
    }


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


def _best_story_ids_for_text(
    text: str,
    story_chunks: list[Chunk],
    story_chunk_vectors: dict[str, dict[int, float]],
    embedding_backend: EmbeddingBackend,
    ranked_story_ids: list[str],
    embedding_cache: EmbeddingCache | None = None,
    top_n: int = 2,
) -> list[str]:
    if not story_chunks:
        return ranked_story_ids[:1]
    query_vec = embedding_cache.get_or_embed(text, embedding_backend) if embedding_cache else embedding_backend.embed(text)
    scored: list[tuple[float, str]] = []
    for chunk in story_chunks:
        semantic = 0.0
        chunk_vec = story_chunk_vectors.get(chunk.chunk_id)
        if chunk_vec:
            semantic = cosine_sparse(query_vec, chunk_vec)
        lexical = lexical_overlap_score(text, chunk.text)
        total = semantic + (0.35 * lexical)
        scored.append((total, chunk.parent_id))
    scored.sort(key=lambda item: item[0], reverse=True)
    ordered: list[str] = []
    for _, story_id in scored:
        if story_id not in ordered:
            ordered.append(story_id)
    if not ordered:
        return ranked_story_ids[:1]
    return ordered[:top_n]


def _parse_jd(path: Path) -> tuple[set[str], list[str]]:
    text, requirements = _load_jd_content(path)
    return _parse_jd_text(text, requirements=requirements)


def build_model(
    base_resume_text: str,
    jd_keywords: set[str],
    jd_requirements: list[str],
    page_budget: int,
    default_location: str,
    story_chunks: list[Chunk],
    story_chunk_vectors: dict[str, dict[int, float]],
    embedding_backend: EmbeddingBackend,
    ranked_story_ids: list[str],
    embedding_cache: EmbeddingCache | None,
) -> dict:
    limits = BUDGET_LIMITS[page_budget]
    basics = _parse_basics(base_resume_text, default_location=default_location)
    about_sentences, highlights = _parse_summary_and_highlights(base_resume_text)
    experience_raw = _parse_experience(base_resume_text)
    education = _parse_education(base_resume_text)
    skills = _parse_skills(experience_raw, highlights)

    summary_candidates = about_sentences + highlights
    jd_query_text = " ".join(jd_requirements).strip()
    if not jd_query_text and jd_keywords:
        jd_query_text = " ".join(sorted(jd_keywords))
    jd_query_vec = _embed_text(jd_query_text, embedding_backend, embedding_cache)

    summary_scored = sorted(
        summary_candidates,
        key=lambda s: (
            _hybrid_score(
                s,
                jd_text=jd_query_text,
                jd_vector=jd_query_vec,
                embedding_backend=embedding_backend,
                embedding_cache=embedding_cache,
            ),
            _score(s, jd_keywords),
            len(s),
        ),
        reverse=True,
    )
    summary_text = summary_scored[: limits["summary_bullets_max"]]
    summary = [{"bullet_id": f"SUM-{idx:03d}", "text": text} for idx, text in enumerate(summary_text, start=1)]

    role_entries = []
    for role in experience_raw:
        role_text = f"{role['title']} {role['company']}"
        role_score = _hybrid_score(
            role_text,
            jd_text=jd_query_text,
            jd_vector=jd_query_vec,
            embedding_backend=embedding_backend,
            embedding_cache=embedding_cache,
        )
        role_score += sum(
            _hybrid_score(
                bullet,
                jd_text=jd_query_text,
                jd_vector=jd_query_vec,
                embedding_backend=embedding_backend,
                embedding_cache=embedding_cache,
            )
            for bullet in role["bullets"]
        )
        bullet_pairs = sorted(
            role["bullets"],
            key=lambda bullet: (
                _hybrid_score(
                    bullet,
                    jd_text=jd_query_text,
                    jd_vector=jd_query_vec,
                    embedding_backend=embedding_backend,
                    embedding_cache=embedding_cache,
                ),
                _score(bullet, jd_keywords),
                len(bullet),
            ),
            reverse=True,
        )
        bullets = bullet_pairs[: limits["experience_bullets_per_role_max"]]
        role_entries.append((role_score, role, bullets))

    role_entries.sort(key=lambda item: item[0], reverse=True)
    selected_role_entries = role_entries[: limits["experience_roles_max"]]
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
            traceability.append(
                {
                    "bullet_id": bullet_id,
                    "story_ids": _best_story_ids_for_text(
                        bullet,
                        story_chunks=story_chunks,
                        story_chunk_vectors=story_chunk_vectors,
                        embedding_backend=embedding_backend,
                        ranked_story_ids=ranked_story_ids,
                        embedding_cache=embedding_cache,
                    ),
                }
            )
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
        traceability.append(
            {
                "bullet_id": item["bullet_id"],
                "story_ids": _best_story_ids_for_text(
                    item["text"],
                    story_chunks=story_chunks,
                    story_chunk_vectors=story_chunk_vectors,
                    embedding_backend=embedding_backend,
                    ranked_story_ids=ranked_story_ids,
                    embedding_cache=embedding_cache,
                ),
            }
        )

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
    parser = argparse.ArgumentParser(description="Tailor a resume model from base resume + JD input.")
    parser.add_argument("--base-resume", required=True, help="Path to base resume markdown.")
    jd_group = parser.add_mutually_exclusive_group(required=True)
    jd_group.add_argument(
        "--job-description",
        help="Path to job description file (.md, .txt, .html, .htm).",
    )
    jd_group.add_argument(
        "--job-description-url",
        help="URL to job description page or text (supports Greenhouse HTML pages).",
    )
    parser.add_argument(
        "--jd-fetch-cache-dir",
        default="~/.cache/resume_story_bank/job_description_fetches",
        help=(
            "Directory for raw --job-description-url fetch artifacts "
            "(default: ~/.cache/resume_story_bank/job_description_fetches)."
        ),
    )
    parser.add_argument(
        "--no-jd-fetch-cache",
        action="store_true",
        help="Disable writing raw --job-description-url fetch artifacts.",
    )
    parser.add_argument(
        "--master-story-bank",
        default="data/processed/master_story_bank.md",
        help="Path to master story bank markdown.",
    )
    parser.add_argument("--output", required=True, help="Path to output resume model JSON.")
    parser.add_argument("--page-budget", type=int, choices=(1, 2), default=2, help="Page budget (default: 2).")
    parser.add_argument("--default-location", default="Remote", help="Fallback location for basics.")
    parser.add_argument("--default-story-id", default="SB-000", help="Fallback story ID.")
    parser.add_argument(
        "--embedding-backend",
        default=os.environ.get("RESUME_SB_EMBEDDING_BACKEND", "local_hash_v1"),
        help="Embedding backend: local_hash_v1 or openai (default from RESUME_SB_EMBEDDING_BACKEND or local_hash_v1).",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        help="Embedding model for OpenAI backend (default: text-embedding-3-small).",
    )
    parser.add_argument(
        "--openai-base-url",
        default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        help="OpenAI base URL (default: https://api.openai.com/v1).",
    )
    parser.add_argument(
        "--openai-api-key",
        default=None,
        help="Optional OpenAI API key override (otherwise OPENAI_API_KEY env var is used).",
    )
    parser.add_argument(
        "--embedding-cache",
        default="~/.cache/resume_story_bank/embedding_cache.json",
        help="Path to persistent embedding cache JSON (default: ~/.cache/resume_story_bank/embedding_cache.json).",
    )
    parser.add_argument(
        "--no-embedding-cache",
        action="store_true",
        help="Disable embedding cache reads/writes for this run.",
    )
    parser.add_argument(
        "--selection-report",
        default=None,
        help="Optional path to write story-selection explanation report JSON.",
    )
    args = parser.parse_args()

    if not STORY_ID_PATTERN.match(args.default_story_id):
        print("ERROR: --default-story-id must match SB-### format")
        return 1

    base_path = Path(args.base_resume)
    jd_path: Path | None = Path(args.job_description) if args.job_description else None
    story_path = Path(args.master_story_bank)
    output_path = Path(args.output)

    if not base_path.exists():
        print(f"ERROR: base resume not found: {base_path}")
        return 1
    if jd_path and not jd_path.exists():
        print(f"ERROR: job description not found: {jd_path}")
        return 1

    base_text = base_path.read_text(encoding="utf-8")
    preflight_errors = _preflight_base_resume(base_text)
    if preflight_errors:
        print("ERROR: base resume format preflight failed")
        for err in preflight_errors:
            print(f"- {err}")
        return 1

    jd_fetch_artifact: dict | None = None
    try:
        if jd_path:
            jd_keywords, jd_requirements = _parse_jd(jd_path)
        else:
            jd_fetch_cache_dir: Path | None = None
            if not args.no_jd_fetch_cache:
                jd_fetch_cache_dir = Path(args.jd_fetch_cache_dir).expanduser()
            jd_keywords, jd_requirements, jd_fetch_artifact = _parse_jd_url(
                args.job_description_url,
                jd_fetch_cache_dir=jd_fetch_cache_dir,
            )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    stories: list[Story]
    if story_path.exists():
        stories = parse_master_story_bank(story_path.read_text(encoding="utf-8"))
    else:
        stories = []
    if not stories:
        stories = [
            Story(
                story_id=args.default_story_id,
                title="Fallback Story",
                context="",
                actions="",
                outcomes="",
                skills_keywords="",
                source_references="",
            )
        ]

    try:
        embedding_backend = create_embedding_backend(
            backend_name=args.embedding_backend,
            openai_model=args.embedding_model,
            openai_api_key=args.openai_api_key or os.environ.get("OPENAI_API_KEY"),
            openai_base_url=args.openai_base_url,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    embedding_cache: EmbeddingCache | None = None
    embedding_cache_path = Path(args.embedding_cache).expanduser()
    if not args.no_embedding_cache:
        embedding_cache = EmbeddingCache(embedding_cache_path)
        embedding_cache.load()

    story_chunks = build_story_chunks(stories)
    base_resume_summary_candidates: list[str] = []
    base_resume_role_texts: list[str] = []
    base_resume_bullets: list[str] = []
    about_sentences_for_cache, highlights_for_cache = _parse_summary_and_highlights(base_text)
    base_resume_summary_candidates.extend(about_sentences_for_cache)
    base_resume_summary_candidates.extend(highlights_for_cache)
    for role in _parse_experience(base_text):
        base_resume_role_texts.append(f"{role['title']} {role['company']}")
        base_resume_bullets.extend(role["bullets"])

    jd_text_for_chunks = " ".join(jd_requirements) if jd_requirements else ""
    jd_chunks = build_jd_chunks(jd_text_for_chunks)
    jd_candidate_texts = [chunk.text for chunk in jd_chunks]
    if jd_text_for_chunks.strip():
        jd_candidate_texts.append(jd_text_for_chunks.strip())

    if embedding_cache:
        story_cache_summary = _cache_reuse_summary(
            texts=[chunk.text for chunk in story_chunks],
            embedding_backend=embedding_backend,
            embedding_cache=embedding_cache,
        )
        jd_cache_summary = _cache_reuse_summary(
            texts=jd_candidate_texts,
            embedding_backend=embedding_backend,
            embedding_cache=embedding_cache,
        )
        base_resume_cache_summary = _cache_reuse_summary(
            texts=base_resume_summary_candidates + base_resume_role_texts + base_resume_bullets,
            embedding_backend=embedding_backend,
            embedding_cache=embedding_cache,
        )
        jd_source_label = str(jd_path) if jd_path else args.job_description_url
        print("Embedding cache precheck:")
        print(
            f"- master story bank ({story_path}): "
            f"{story_cache_summary['hits']}/{story_cache_summary['total']} cached, "
            f"{story_cache_summary['misses']} to embed"
        )
        print(
            f"- job description ({jd_source_label}): "
            f"{jd_cache_summary['hits']}/{jd_cache_summary['total']} cached, "
            f"{jd_cache_summary['misses']} to embed"
        )
        print(
            f"- base resume ({base_path}): "
            f"{base_resume_cache_summary['hits']}/{base_resume_cache_summary['total']} cached, "
            f"{base_resume_cache_summary['misses']} to embed"
        )

    try:
        story_chunk_vectors = {
            chunk.chunk_id: (
                embedding_cache.get_or_embed(chunk.text, embedding_backend)
                if embedding_cache
                else embedding_backend.embed(chunk.text)
            )
            for chunk in story_chunks
        }
        ranked_stories = rank_stories_for_jd(
            jd_chunks=jd_chunks,
            stories=stories,
            story_chunks=story_chunks,
            embedding_backend=embedding_backend,
            cache=embedding_cache,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: embedding step failed: {exc}")
        return 1
    ranked_story_ids = [item["story_id"] for item in ranked_stories] or [args.default_story_id]

    model = build_model(
        base_resume_text=base_text,
        jd_keywords=jd_keywords,
        jd_requirements=jd_requirements,
        page_budget=args.page_budget,
        default_location=args.default_location,
        story_chunks=story_chunks,
        story_chunk_vectors=story_chunk_vectors,
        embedding_backend=embedding_backend,
        ranked_story_ids=ranked_story_ids,
        embedding_cache=embedding_cache,
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

    report = create_selection_report(
        jd_text=" ".join(jd_requirements),
        ranked_stories=ranked_stories,
        embedding_backend_name=embedding_backend.name,
    )
    if embedding_cache:
        report["embedding_cache"] = {
            "path": str(embedding_cache_path),
            "hits": embedding_cache.hits,
            "misses": embedding_cache.misses,
        }
    if jd_fetch_artifact:
        report["job_description_fetch"] = jd_fetch_artifact
    report_path = Path(args.selection_report) if args.selection_report else output_path.with_name("selection_report.json")
    report_path.write_text(dumps_pretty(report), encoding="utf-8")
    print(f"Wrote selection report: {report_path}")
    if jd_fetch_artifact:
        print(f"Saved JD fetch artifact: {jd_fetch_artifact['raw_path']}")
        print(f"Saved JD fetch metadata: {jd_fetch_artifact['metadata_path']}")
    if embedding_cache:
        embedding_cache.save()
        print(f"Updated embedding cache: {embedding_cache_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
