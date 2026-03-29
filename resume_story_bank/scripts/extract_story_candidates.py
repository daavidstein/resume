#!/usr/bin/env python3
"""Generate draft story-bank entries from raw transcript-style markdown/text.

This script is intentionally deterministic and standard-library-only.
It does not write directly to master_story_bank.md; it emits candidate entries
for human review and merge.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


STORY_ID_PATTERN = re.compile(r"\bSB-(\d{3,})\b")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
WORD_PATTERN = re.compile(r"[A-Za-z0-9_+/.-]+")

ACTION_VERBS = {
    "architected",
    "automated",
    "built",
    "co-led",
    "collaborated",
    "created",
    "deployed",
    "delivered",
    "designed",
    "developed",
    "drove",
    "established",
    "evaluated",
    "implemented",
    "improved",
    "launched",
    "led",
    "managed",
    "mentored",
    "optimized",
    "owned",
    "proposed",
    "reduced",
    "shipped",
    "trained",
}

KEYWORD_HINTS = {
    "python",
    "sql",
    "aws",
    "pytorch",
    "tensorflow",
    "llm",
    "nlp",
    "etl",
    "airflow",
    "spark",
    "dbt",
    "ci/cd",
    "metaflow",
    "sagemaker",
    "redshift",
    "dynamodb",
    "lambda",
    "flask",
    "fastapi",
    "experiment",
    "a/b",
    "dashboard",
}

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
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


@dataclass
class CandidateUnit:
    text: str
    line_no: int


@dataclass
class CandidateStory:
    title: str
    context: str
    action: str
    outcomes: list[str]
    skills: list[str]
    source_reference: str
    source_line: int
    open_questions: list[str]


def _next_story_id(master_story_bank_text: str) -> int:
    numbers = [int(match.group(1)) for match in STORY_ID_PATTERN.finditer(master_story_bank_text)]
    if not numbers:
        return 1
    return max(numbers) + 1


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in WORD_PATTERN.findall(text)]


def _normalize_line(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _extract_units(transcript_text: str) -> list[CandidateUnit]:
    units: list[CandidateUnit] = []
    for idx, raw_line in enumerate(transcript_text.splitlines(), start=1):
        line = _normalize_line(raw_line)
        if not line:
            continue
        if line.startswith("- "):
            line = _normalize_line(line[2:])
            if line:
                units.append(CandidateUnit(text=line, line_no=idx))
            continue
        for part in SENTENCE_SPLIT_PATTERN.split(line):
            sentence = _normalize_line(part)
            if sentence:
                units.append(CandidateUnit(text=sentence, line_no=idx))
    return units


def _score_unit(text: str) -> int:
    lower = text.lower()
    tokens = set(_tokenize(lower))
    score = 0

    if any(verb in lower or verb in tokens for verb in ACTION_VERBS):
        score += 3
    if re.search(r"\d", text):
        score += 2
    if any(symbol in text for symbol in ("%", "$", "x", "X")):
        score += 1
    word_count = len(_tokenize(text))
    if 8 <= word_count <= 40:
        score += 1
    return score


def _extract_keywords(text: str) -> list[str]:
    lower = text.lower()
    found: set[str] = set()
    for hint in KEYWORD_HINTS:
        if hint in lower:
            found.add(hint.upper() if hint.isalpha() and len(hint) <= 4 else hint)
    if not found:
        tokens = [tok for tok in _tokenize(text) if len(tok) > 3 and tok not in STOPWORDS]
        found.update(tokens[:4])
    return sorted(found)


def _title_from_text(text: str) -> str:
    tokens = [tok for tok in _tokenize(text) if tok not in STOPWORDS]
    if not tokens:
        return "Candidate Story"
    clipped = tokens[:6]
    return " ".join(token.capitalize() for token in clipped)


def extract_story_candidates(
    transcript_text: str,
    source_reference: str,
    existing_master_story_bank_text: str,
    max_stories: int = 6,
) -> list[CandidateStory]:
    units = _extract_units(transcript_text)
    master_lower = existing_master_story_bank_text.lower()
    seen_texts: set[str] = set()
    ranked: list[tuple[int, CandidateUnit]] = []

    for unit in units:
        normalized = unit.text.lower()
        if normalized in seen_texts:
            continue
        seen_texts.add(normalized)
        if normalized in master_lower:
            continue
        score = _score_unit(unit.text)
        if score >= 3:
            ranked.append((score, unit))

    ranked.sort(key=lambda item: (item[0], len(item[1].text)), reverse=True)
    selected = ranked[:max_stories]

    stories: list[CandidateStory] = []
    for _, unit in selected:
        outcomes: list[str] = []
        questions: list[str] = []
        if re.search(r"\d", unit.text):
            outcomes.append(f"Observed outcome signal from transcript: {unit.text}")
        else:
            outcomes.append("Outcome metric: TBD")
            questions.append("What measurable metric or business impact can be attached to this story?")

        stories.append(
            CandidateStory(
                title=_title_from_text(unit.text),
                context="Context from interview transcript. Confirm scope, constraints, and timeline.",
                action=unit.text,
                outcomes=outcomes,
                skills=_extract_keywords(unit.text),
                source_reference=source_reference,
                source_line=unit.line_no,
                open_questions=questions,
            )
        )
    return stories


def render_story_candidates_markdown(
    stories: list[CandidateStory],
    starting_story_number: int,
) -> str:
    lines: list[str] = []
    lines.append("# Candidate Story Extraction")
    lines.append("")
    lines.append("## Candidate Story Entries")
    lines.append("")

    for idx, story in enumerate(stories):
        story_number = starting_story_number + idx
        story_id = f"SB-{story_number:03d}"
        lines.append(f"## Story: {story.title}")
        lines.append("")
        lines.append("### Story ID")
        lines.append(story_id)
        lines.append("")
        lines.append("### Context")
        lines.append(story.context)
        lines.append("")
        lines.append("### Actions")
        lines.append(f"- {story.action}")
        lines.append("")
        lines.append("### Outcomes")
        for outcome in story.outcomes:
            lines.append(f"- {outcome}")
        lines.append("")
        lines.append("### Skills/Keywords")
        lines.append(", ".join(story.skills) if story.skills else "TBD")
        lines.append("")
        lines.append("### Source References")
        lines.append(f"- `{story.source_reference}`")
        lines.append("")
        lines.append("### Tailoring Notes (Optional)")
        lines.append("- Best-fit role types:")
        lines.append("- Useful keywords:")
        lines.append("- Caveats:")
        lines.append("")

    lines.append("## Mapping Notes")
    lines.append("")
    for idx, story in enumerate(stories):
        story_number = starting_story_number + idx
        story_id = f"SB-{story_number:03d}"
        lines.append(
            f"- {story_id} <- {story.source_reference}:line {story.source_line}"
        )
    lines.append("")

    open_questions = [question for story in stories for question in story.open_questions]
    lines.append("## Open Questions")
    lines.append("")
    if open_questions:
        for question in sorted(set(open_questions)):
            lines.append(f"- {question}")
    else:
        lines.append("- None identified by heuristic extraction.")
    lines.append("")
    return "\n".join(lines)


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _resolve_input_path(path_value: str, repo_root: Path) -> Path:
    provided = Path(path_value)
    if provided.exists():
        return provided
    candidate = repo_root / provided
    if candidate.exists():
        return candidate
    return provided


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract candidate story entries from transcript markdown/text."
    )
    parser.add_argument(
        "--input",
        required=True,
        nargs="+",
        help="One or more transcript file paths.",
    )
    parser.add_argument(
        "--master-story-bank",
        default="data/processed/master_story_bank.md",
        help="Path to existing master story bank markdown.",
    )
    parser.add_argument(
        "--max-stories",
        type=int,
        default=6,
        help="Maximum candidate stories to emit across all inputs.",
    )
    parser.add_argument(
        "--output",
        help="Optional output markdown path. Defaults to stdout.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    master_path = _resolve_input_path(args.master_story_bank, repo_root)
    if not master_path.exists():
        print(f"ERROR: master story bank not found: {master_path}")
        return 1
    master_text = _load_text(master_path)
    starting_number = _next_story_id(master_text)

    input_paths = [_resolve_input_path(path, repo_root) for path in args.input]
    missing = [path for path in input_paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"ERROR: input transcript not found: {path}")
        return 1

    all_stories: list[CandidateStory] = []
    for input_path in input_paths:
        raw_text = _load_text(input_path)
        source_ref = str(input_path)
        stories = extract_story_candidates(
            transcript_text=raw_text,
            source_reference=source_ref,
            existing_master_story_bank_text=master_text,
            max_stories=max(args.max_stories, 1),
        )
        all_stories.extend(stories)

    all_stories = all_stories[: max(args.max_stories, 1)]
    markdown = render_story_candidates_markdown(
        stories=all_stories,
        starting_story_number=starting_number,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote candidate stories: {output_path}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
