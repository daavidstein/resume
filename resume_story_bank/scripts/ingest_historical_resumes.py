#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from historical_resume_pipeline import (
    collect_resume_paths,
    extract_historical_bullet_inventory,
    render_historical_inventory_markdown,
    write_output_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="append", default=[], help="Resume path (.md, .txt, .pdf). Repeatable.")
    parser.add_argument("--resume-dir", help="Directory of historical resumes to ingest.")
    parser.add_argument("--output", required=True, help="Output artifact path (.json or .md base).")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format to write.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = collect_resume_paths(args.resume, args.resume_dir)
    if not paths:
        print("ERROR: no resume inputs found")
        return 1
    inventory = extract_historical_bullet_inventory(paths)
    written = write_output_bundle(
        inventory,
        Path(args.output).expanduser(),
        args.format,
        render_historical_inventory_markdown,
    )
    for path in written:
        print(f"WROTE: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
