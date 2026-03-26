#!/usr/bin/env python3
"""Placeholder utility for future story-file splitting.

Current behavior:
- Prints planned actions only.
- Does not write any files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


STORY_HEADER_PATTERN = re.compile(r"^## Story:\s+(.+)$")


def count_stories(text: str) -> int:
    return sum(1 for line in text.splitlines() if STORY_HEADER_PATTERN.match(line))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview how master_story_bank.md could be split in the future."
    )
    parser.add_argument(
        "--input",
        default="data/processed/master_story_bank.md",
        help="Path to the master story bank markdown file (repo-relative).",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/stories",
        help="Target directory for per-story files (future behavior).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show intended behavior only (default: true).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / args.input
    output_dir = repo_root / args.output_dir

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        return 1

    text = input_path.read_text(encoding="utf-8")
    story_count = count_stories(text)

    print("split_story_bank.py is currently a placeholder.")
    print(f"- Input: {input_path}")
    print(f"- Stories detected: {story_count}")
    print(f"- Planned output dir: {output_dir}")
    print("- No files were written.")
    print(
        "- Future version will split each '## Story: ...' block into one markdown file "
        "while preserving Story ID and metadata."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
