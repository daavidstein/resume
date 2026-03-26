#!/usr/bin/env python3
"""Lightweight validator for data/processed/master_story_bank.md.

Checks:
- Each story has a Story ID.
- Required section headers exist for each story.
- Story IDs are unique.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_HEADERS = [
    "### Story ID",
    "### Context",
    "### Actions",
    "### Outcomes",
    "### Skills/Keywords",
    "### Source References",
]

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


def validate_block(block: StoryBlock) -> list[str]:
    errors: list[str] = []
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

    return errors


def main() -> int:
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
    ids: list[tuple[str, StoryBlock]] = []

    for block in blocks:
        errors.extend(validate_block(block))
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
        return 1

    print(f"VALIDATION PASSED: {len(blocks)} story block(s), {len(seen)} unique ID(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
