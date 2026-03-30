#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from historical_resume_pipeline import (
    generate_candidate_bullet_batch,
    load_job_context,
    load_json_artifact,
    load_story_bank,
    render_candidate_bullets_markdown,
    write_output_bundle_with_story_context,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--linked-historical-bullets", required=True, help="Linked historical bullet inventory JSON.")
    parser.add_argument("--master-story-bank", required=True, help="Story bank markdown path.")
    parser.add_argument("--output", required=True, help="Output artifact path.")
    parser.add_argument("--job-description", help="Optional JD file path.")
    parser.add_argument("--job-description-url", help="Optional JD URL.")
    parser.add_argument("--story-ids", help="Optional comma-separated story IDs to target.")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format to write.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inventory = load_json_artifact(Path(args.linked_historical_bullets).expanduser())
    stories = load_story_bank(Path(args.master_story_bank).expanduser())
    jd_text, job_context = load_job_context(args.job_description, args.job_description_url)
    selected_story_ids = None
    if args.story_ids:
        selected_story_ids = {item.strip() for item in args.story_ids.split(",") if item.strip()}
    batch = generate_candidate_bullet_batch(
        inventory,
        stories,
        jd_text=jd_text,
        job_context=job_context,
        selected_story_ids=selected_story_ids,
    )
    written = write_output_bundle_with_story_context(
        batch,
        Path(args.output).expanduser(),
        args.format,
        render_candidate_bullets_markdown,
        stories,
    )
    for path in written:
        print(f"WROTE: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
