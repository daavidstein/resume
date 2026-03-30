#!/usr/bin/env python3
"""Lightweight validator for data/processed/master_story_bank.md.

Checks:
- Each story has a Story ID.
- Required section headers exist for each story.
- Story IDs are unique.
- Structured metadata is validated in staged migration mode by default.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from metadata_ontology import (
    load_tag_ontology,
    normalize_structured_metadata,
    validate_structured_metadata_against_ontology,
)
from rag_retrieval import parse_structured_metadata


REQUIRED_HEADERS = [
    "### Story ID",
    "### Context",
    "### Actions",
    "### Outcomes",
    "### Skills/Keywords",
    "### Source References",
]

STRUCTURED_METADATA_HEADER = "### Structured Metadata"

STRUCTURED_METADATA_LIST_FIELDS = {
    "role_family_tags",
    "domain_tags",
    "capability_tags",
    "technology_tags",
    "business_problem_tags",
    "audience_tags",
    "preferred_resume_angles",
    "wording_constraints",
    "caveats",
    "forbidden_claims",
}

STRUCTURED_METADATA_SCALAR_FIELDS = {
    "ownership_level": {
        "supporting",
        "individual_contributor",
        "cross_functional_driver",
        "technical_lead",
    },
    "seniority_scope": {"junior", "mid", "senior", "mixed"},
    "evidence_strength": {"strong", "medium", "weak"},
    "recency_bucket": {"current", "recent", "older", "timeless"},
    "rewrite_safety": {"high", "medium", "low"},
}

STRUCTURED_METADATA_REQUIRED_KEYS = (
    sorted(STRUCTURED_METADATA_LIST_FIELDS)
    + sorted(STRUCTURED_METADATA_SCALAR_FIELDS)
)

STORY_HEADER_PATTERN = re.compile(r"^## Story:\s+.+$")
ID_PATTERN = re.compile(r"^SB-\d{3,}$")


@dataclass
class StoryBlock:
    title: str
    lines: list[str]
    start_line: int


def parse_story_blocks(text: str) -> list[StoryBlock]:
    lines = text.splitlines()
    blocks: list[StoryBlock] = []
    current_title: str | None = None
    current_lines: list[str] = []
    current_start = 0

    for idx, line in enumerate(lines, start=1):
        if STORY_HEADER_PATTERN.match(line):
            if current_title is not None:
                blocks.append(
                    StoryBlock(
                        title=current_title,
                        lines=current_lines,
                        start_line=current_start,
                    )
                )
            current_title = line.replace("## Story:", "", 1).strip()
            current_lines = [line]
            current_start = idx
            continue

        if current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        blocks.append(
            StoryBlock(title=current_title, lines=current_lines, start_line=current_start)
        )

    return blocks


def extract_story_id(block: StoryBlock) -> str | None:
    for idx, line in enumerate(block.lines):
        if line.strip() == "### Story ID":
            # Story ID value should be the next non-empty line.
            for follow in block.lines[idx + 1 :]:
                candidate = follow.strip()
                if candidate:
                    return candidate
            return None
    return None


def extract_section_value(block: StoryBlock, header: str) -> str:
    pattern = re.compile(rf"(?ms)^### {re.escape(header)}\s*$\n(.*?)(?=^### |\Z)")
    body = "\n".join(block.lines)
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def validate_block(block: StoryBlock, strict_structured_metadata: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    body = "\n".join(block.lines)

    for header in REQUIRED_HEADERS:
        if header not in body:
            errors.append(
                f"Line {block.start_line}: '{block.title}' missing required header: {header}"
            )

    story_id = extract_story_id(block)
    if not story_id:
        errors.append(f"Line {block.start_line}: '{block.title}' missing story ID value")
    elif not ID_PATTERN.match(story_id):
        errors.append(
            f"Line {block.start_line}: '{block.title}' has invalid story ID format: {story_id}"
        )

    metadata_block = extract_section_value(block, "Structured Metadata")
    if not metadata_block:
        if strict_structured_metadata:
            errors.append(
                f"Line {block.start_line}: '{block.title}' missing required header: {STRUCTURED_METADATA_HEADER}"
            )
        else:
            warnings.append(
                f"Line {block.start_line}: '{block.title}' is missing {STRUCTURED_METADATA_HEADER}; tolerated during Phase 1 migration"
            )
        return errors, warnings

    try:
        metadata = parse_structured_metadata(metadata_block)
    except ValueError as exc:
        errors.append(
            f"Line {block.start_line}: '{block.title}' has invalid Structured Metadata: {exc}"
        )
        return errors, warnings

    ontology, ontology_load_warnings = load_tag_ontology()
    warnings.extend(
        f"Line {block.start_line}: '{block.title}' ontology warning: {warning}"
        for warning in ontology_load_warnings
    )
    metadata, normalization_warnings = normalize_structured_metadata(
        metadata, ontology=ontology
    )
    warnings.extend(
        f"Line {block.start_line}: '{block.title}' metadata normalization warning: {warning}"
        for warning in normalization_warnings
    )
    warnings.extend(
        f"Line {block.start_line}: '{block.title}' ontology warning: {warning}"
        for warning in validate_structured_metadata_against_ontology(metadata, ontology)
    )

    missing_keys = [key for key in STRUCTURED_METADATA_REQUIRED_KEYS if key not in metadata]
    if missing_keys:
        errors.append(
            f"Line {block.start_line}: '{block.title}' Structured Metadata is missing required key(s): {', '.join(missing_keys)}"
        )

    for key in sorted(metadata):
        value = metadata[key]
        if key in STRUCTURED_METADATA_LIST_FIELDS:
            if not isinstance(value, list):
                errors.append(
                    f"Line {block.start_line}: '{block.title}' field '{key}' must use bracket list syntax like [tag_one, tag_two]"
                )
        elif key in STRUCTURED_METADATA_SCALAR_FIELDS:
            if isinstance(value, list):
                errors.append(
                    f"Line {block.start_line}: '{block.title}' field '{key}' must be a scalar enum value, not a list"
                )
                continue
            allowed = STRUCTURED_METADATA_SCALAR_FIELDS[key]
            if value not in allowed:
                errors.append(
                    f"Line {block.start_line}: '{block.title}' field '{key}' must be one of: {', '.join(sorted(allowed))}; got '{value}'"
                )
        else:
            errors.append(
                f"Line {block.start_line}: '{block.title}' has unknown Structured Metadata key: {key}"
            )

    return errors, warnings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-structured-metadata",
        action="store_true",
        help="Require every story to include a fully populated Structured Metadata block.",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "data" / "processed" / "master_story_bank.md"

    if not target.exists():
        print(f"ERROR: missing file: {target}")
        return 1

    text = target.read_text(encoding="utf-8")
    blocks = parse_story_blocks(text)
    if not blocks:
        print("ERROR: no stories found. Expected headings like '## Story: ...'")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    ids: list[tuple[str, StoryBlock]] = []

    for block in blocks:
        block_errors, block_warnings = validate_block(
            block, strict_structured_metadata=args.strict_structured_metadata
        )
        errors.extend(block_errors)
        warnings.extend(block_warnings)
        story_id = extract_story_id(block)
        if story_id:
            ids.append((story_id, block))

    seen: dict[str, StoryBlock] = {}
    for story_id, block in ids:
        if story_id in seen:
            original = seen[story_id]
            errors.append(
                "Duplicate story ID "
                f"{story_id}: line {original.start_line} ('{original.title}') "
                f"and line {block.start_line} ('{block.title}')"
            )
        else:
            seen[story_id] = block

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        if warnings:
            print("WARNINGS")
            for warning in warnings:
                print(f"- {warning}")
        return 1

    if warnings:
        print("VALIDATION PASSED WITH WARNINGS")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("VALIDATION PASSED")
    print(
        f"Summary: {len(blocks)} story block(s), {len(seen)} unique ID(s), "
        f"strict_structured_metadata={args.strict_structured_metadata}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
