#!/usr/bin/env python3
"""Lightweight retrieval utilities for JD-to-story matching.

This module keeps dependencies in the standard library only and exposes a
provider-agnostic embedding interface so a future backend can replace the local
hash embedding without changing the pipeline shape.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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

STORY_HEADER_PATTERN = re.compile(r"^## Story:\s+(.+)$", re.MULTILINE)


@dataclass
class Story:
    story_id: str
    title: str
    context: str
    actions: str
    outcomes: str
    skills_keywords: str
    source_references: str

    @property
    def full_text(self) -> str:
        return "\n".join(
            [
                self.title,
                self.context,
                self.actions,
                self.outcomes,
                self.skills_keywords,
            ]
        )


@dataclass
class Chunk:
    chunk_id: str
    parent_id: str
    label: str
    text: str


class EmbeddingBackend(Protocol):
    name: str

    def embed(self, text: str) -> dict[int, float]:
        """Embed text as a sparse normalized vector."""


def _tokens(text: str) -> list[str]:
    return [
        tok
        for tok in re.findall(r"[a-zA-Z][a-zA-Z0-9+#/.-]*", text.lower())
        if len(tok) > 2 and tok not in STOPWORDS
    ]


class LocalHashEmbeddingBackend:
    """Simple deterministic sparse hash embedding."""

    name = "local_hash_v1"

    def __init__(self, dimensions: int = 2048, include_bigrams: bool = True) -> None:
        self.dimensions = dimensions
        self.include_bigrams = include_bigrams

    def embed(self, text: str) -> dict[int, float]:
        tokens = _tokens(text)
        features = list(tokens)
        if self.include_bigrams:
            features.extend(f"{tokens[i]}::{tokens[i + 1]}" for i in range(len(tokens) - 1))
        if not features:
            return {}

        vec: dict[int, float] = {}
        for feat in features:
            digest = hashlib.sha256(feat.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:8], "big") % self.dimensions
            vec[idx] = vec.get(idx, 0.0) + 1.0

        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm <= 0:
            return {}
        return {idx: val / norm for idx, val in vec.items()}


class OpenAIEmbeddingBackend:
    """OpenAI embeddings backend using the REST API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 30,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.name = f"openai_{self.model}"

    def embed(self, text: str) -> dict[int, float]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for openai embedding backend")

        payload = {
            "model": self.model,
            "input": text,
        }
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/embeddings",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI embeddings request failed ({exc.code}): {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"OpenAI embeddings request failed: {exc}") from exc

        data = json.loads(raw)
        vector = data["data"][0]["embedding"]
        norm = math.sqrt(sum(float(v) * float(v) for v in vector))
        if norm <= 0:
            return {}
        return {idx: float(val) / norm for idx, val in enumerate(vector)}


class EmbeddingCache:
    """Persistent embedding cache keyed by backend name and SHA-256 of input text.

    Key format:
    - ``{backend_name}:{sha256_hex}``
    - Example: ``openai_text-embedding-3-small:d743...``

    Hash input details:
    - SHA-256 is computed over the exact ``text.encode("utf-8")`` bytes passed to
      ``get_or_embed``.
    - No canonicalization is applied (no whitespace normalization, lowercasing, or
      punctuation cleanup), so any text change produces a different key.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.records: dict[str, dict[str, float]] = {}
        self._loaded = False
        self.hits = 0
        self.misses = 0

    def load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.path.exists():
            self.records = {}
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.records = {}
            return
        if isinstance(data, dict) and isinstance(data.get("records"), dict):
            self.records = data["records"]
        else:
            self.records = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "records": self.records,
        }
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _key(text: str, backend_name: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{backend_name}:{digest}"

    def get_or_embed(self, text: str, backend: EmbeddingBackend) -> dict[int, float]:
        self.load()
        key = self._key(text, backend.name)
        if key in self.records:
            self.hits += 1
            raw = self.records[key]
            return {int(idx): float(val) for idx, val in raw.items()}
        self.misses += 1
        vector = backend.embed(text)
        self.records[key] = {str(idx): val for idx, val in vector.items()}
        return vector


def cosine_sparse(a: dict[int, float], b: dict[int, float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    dot = 0.0
    for idx, val in a.items():
        other = b.get(idx)
        if other is not None:
            dot += val * other
    return dot


def lexical_overlap_score(a_text: str, b_text: str) -> float:
    a = set(_tokens(a_text))
    b = set(_tokens(b_text))
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def parse_master_story_bank(text: str) -> list[Story]:
    chunks = re.split(r"(?m)^## Story:\s+", text)
    stories: list[Story] = []
    for raw in chunks[1:]:
        lines = raw.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        body = "\n".join(lines[1:])
        story_id = _extract_section_value(body, "Story ID")
        if not story_id:
            continue
        stories.append(
            Story(
                story_id=story_id,
                title=title,
                context=_extract_section_value(body, "Context"),
                actions=_extract_section_value(body, "Actions"),
                outcomes=_extract_section_value(body, "Outcomes"),
                skills_keywords=_extract_section_value(body, "Skills/Keywords"),
                source_references=_extract_section_value(body, "Source References"),
            )
        )
    return stories


def _extract_section_value(text: str, section_name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^### {re.escape(section_name)}\s*$\n(.*?)(?=^### |\Z)"
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def build_story_chunks(stories: list[Story]) -> list[Chunk]:
    out: list[Chunk] = []
    for story in stories:
        section_pairs = [
            ("title", story.title),
            ("context", story.context),
            ("actions", story.actions),
            ("outcomes", story.outcomes),
            ("skills_keywords", story.skills_keywords),
        ]
        for label, text in section_pairs:
            if text.strip():
                out.append(
                    Chunk(
                        chunk_id=f"{story.story_id}:{label}",
                        parent_id=story.story_id,
                        label=label,
                        text=text.strip(),
                    )
                )
    return out


def build_jd_chunks(text: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        cleaned = line.strip()
        if not cleaned:
            continue
        label = "line"
        payload = cleaned
        if cleaned.startswith("- "):
            label = "bullet"
            payload = cleaned[2:].strip()
        elif cleaned.startswith("#"):
            label = "heading"
            payload = cleaned.lstrip("#").strip()
        chunks.append(
            Chunk(
                chunk_id=f"jd:{idx}",
                parent_id="jd",
                label=label,
                text=payload,
            )
        )
    if not chunks:
        chunks.append(Chunk(chunk_id="jd:0", parent_id="jd", label="body", text=text.strip()))
    return chunks


def rank_stories_for_jd(
    jd_chunks: list[Chunk],
    stories: list[Story],
    story_chunks: list[Chunk],
    embedding_backend: EmbeddingBackend,
    cache: EmbeddingCache | None = None,
    top_k_per_jd_chunk: int = 5,
) -> list[dict]:
    story_chunk_vectors = {
        chunk.chunk_id: (cache.get_or_embed(chunk.text, embedding_backend) if cache else embedding_backend.embed(chunk.text))
        for chunk in story_chunks
    }
    jd_vectors = {
        chunk.chunk_id: (cache.get_or_embed(chunk.text, embedding_backend) if cache else embedding_backend.embed(chunk.text))
        for chunk in jd_chunks
    }

    per_story: dict[str, dict] = {
        story.story_id: {
            "story_id": story.story_id,
            "story_title": story.title,
            "semantic_score": 0.0,
            "lexical_score": 0.0,
            "top_jd_matches": [],
        }
        for story in stories
    }
    for jd_chunk in jd_chunks:
        jd_vec = jd_vectors[jd_chunk.chunk_id]
        scored_matches: list[tuple[float, Chunk]] = []
        for story_chunk in story_chunks:
            sim = cosine_sparse(jd_vec, story_chunk_vectors[story_chunk.chunk_id])
            if sim > 0:
                scored_matches.append((sim, story_chunk))
        scored_matches.sort(key=lambda item: item[0], reverse=True)
        for sim, story_chunk in scored_matches[:top_k_per_jd_chunk]:
            lexical = lexical_overlap_score(jd_chunk.text, story_chunk.text)
            aggregate = per_story[story_chunk.parent_id]
            aggregate["semantic_score"] += sim
            aggregate["lexical_score"] += lexical
            aggregate["top_jd_matches"].append(
                {
                    "jd_chunk_id": jd_chunk.chunk_id,
                    "jd_chunk_label": jd_chunk.label,
                    "jd_text": jd_chunk.text,
                    "matched_story_chunk_id": story_chunk.chunk_id,
                    "matched_story_chunk_label": story_chunk.label,
                    "semantic_similarity": round(sim, 6),
                    "lexical_overlap": round(lexical, 6),
                }
            )

    ranked = []
    for story in stories:
        row = per_story[story.story_id]
        total = row["semantic_score"] + (0.35 * row["lexical_score"])
        row["score"] = round(total, 6)
        row["semantic_score"] = round(row["semantic_score"], 6)
        row["lexical_score"] = round(row["lexical_score"], 6)
        row["top_jd_matches"] = sorted(
            row["top_jd_matches"], key=lambda item: item["semantic_similarity"], reverse=True
        )[:5]
        ranked.append(row)

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def create_selection_report(
    jd_text: str,
    ranked_stories: list[dict],
    embedding_backend_name: str,
    top_n: int = 10,
) -> dict:
    return {
        "embedding_backend": embedding_backend_name,
        "jd_excerpt": jd_text[:1000],
        "ranked_stories": ranked_stories[:top_n],
    }


def serialize_vectors(chunks: list[Chunk], backend: EmbeddingBackend) -> dict:
    return {
        "embedding_backend": backend.name,
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "parent_id": chunk.parent_id,
                "label": chunk.label,
                "text": chunk.text,
                "embedding": backend.embed(chunk.text),
            }
            for chunk in chunks
        ],
    }


def dumps_pretty(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def create_embedding_backend(
    backend_name: str,
    openai_model: str = "text-embedding-3-small",
    openai_api_key: str | None = None,
    openai_base_url: str = "https://api.openai.com/v1",
) -> EmbeddingBackend:
    normalized = backend_name.strip().lower()
    if normalized in {"local", "local_hash_v1"}:
        return LocalHashEmbeddingBackend()
    if normalized in {"openai", "openai_embeddings"}:
        return OpenAIEmbeddingBackend(
            model=openai_model,
            api_key=openai_api_key,
            base_url=openai_base_url,
        )
    raise ValueError(f"Unsupported embedding backend: {backend_name}")
