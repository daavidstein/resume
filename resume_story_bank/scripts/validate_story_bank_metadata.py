#!/usr/bin/env python3
"""Validate master story bank metadata consistency.

Checks:
- Every Story ID in master_story_bank.md exists in source_map.md.
- source_map.md does not contain unknown Story IDs.
- Every Story ID in master_story_bank.md appears in story_bank_changelog.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


STORY_ID_PATTERN = re.compile(r"SB-\d{3,}")


def _extract_story_ids(text: str) -> set[str]:
    return set(STORY_ID_PATTERN.findall(text))


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    master_path = repo_root / "data" / "processed" / "master_story_bank.md"
    source_map_path = repo_root / "data" / "processed" / "source_map.md"
    changelog_path = repo_root / "data" / "processed" / "story_bank_changelog.md"

    for path in (master_path, source_map_path, changelog_path):
        if not path.exists():
            print(f"ERROR: missing file: {path}")
            return 1

    master_ids = _extract_story_ids(master_path.read_text(encoding="utf-8"))
    source_map_ids = _extract_story_ids(source_map_path.read_text(encoding="utf-8"))
    changelog_ids = _extract_story_ids(changelog_path.read_text(encoding="utf-8"))

    errors: list[str] = []
    missing_from_source_map = sorted(master_ids - source_map_ids)
    unknown_in_source_map = sorted(source_map_ids - master_ids)
    missing_from_changelog = sorted(master_ids - changelog_ids)

    if missing_from_source_map:
        errors.append(
            "Story IDs missing from source_map.md: " + ", ".join(missing_from_source_map)
        )
    if unknown_in_source_map:
        errors.append(
            "Story IDs in source_map.md not found in master_story_bank.md: "
            + ", ".join(unknown_in_source_map)
        )
    if missing_from_changelog:
        errors.append(
            "Story IDs missing from story_bank_changelog.md: "
            + ", ".join(missing_from_changelog)
        )

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "VALIDATION PASSED: metadata is consistent for "
        f"{len(master_ids)} story ID(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
