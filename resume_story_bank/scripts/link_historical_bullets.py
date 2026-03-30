#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from historical_resume_pipeline import (
    link_historical_bullets,
    load_json_artifact,
    load_story_bank,
    render_linked_inventory_markdown,
    write_output_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-bullets", required=True, help="Historical bullet inventory JSON.")
    parser.add_argument("--master-story-bank", required=True, help="Story bank markdown path.")
    parser.add_argument("--output", required=True, help="Output artifact path.")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format to write.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inventory = load_json_artifact(Path(args.historical_bullets).expanduser())
    stories = load_story_bank(Path(args.master_story_bank).expanduser())
    linked = link_historical_bullets(inventory, stories)
    written = write_output_bundle(
        linked,
        Path(args.output).expanduser(),
        args.format,
        render_linked_inventory_markdown,
    )
    for path in written:
        print(f"WROTE: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
