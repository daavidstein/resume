#!/usr/bin/env python3
"""Generate resume artifacts from a structured resume model JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from export_pdf import export_markdown_to_pdf
from render_resume_md import render_markdown
from validate_resume_model import BUDGET_LIMITS, validate_model


def _load_model(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Resume model root must be a JSON object")
    return data


def _apply_budget_compaction(model: dict, page_budget: int) -> dict:
    """Apply deterministic trimming for requested page budget."""
    limits = BUDGET_LIMITS[page_budget]
    compacted = json.loads(json.dumps(model))
    compacted["page_budget"] = page_budget

    summary = compacted.get("summary", [])
    if isinstance(summary, list):
        compacted["summary"] = summary[: limits["summary_bullets_max"]]

    experience = compacted.get("experience", [])
    if isinstance(experience, list):
        trimmed_roles = experience[: limits["experience_roles_max"]]
        for role in trimmed_roles:
            bullets = role.get("bullets", [])
            if isinstance(bullets, list):
                role["bullets"] = bullets[: limits["experience_bullets_per_role_max"]]
        compacted["experience"] = trimmed_roles

    skills = compacted.get("skills", {})
    if isinstance(skills, dict):
        groups = skills.get("groups", [])
        if isinstance(groups, list):
            trimmed_groups = groups[: limits["skills_groups_max"]]
            total_items = 0
            for group in trimmed_groups:
                items = group.get("items", [])
                if not isinstance(items, list):
                    continue
                remaining = max(0, limits["skills_items_total_max"] - total_items)
                if len(items) > remaining:
                    group["items"] = items[:remaining]
                total_items += len(group.get("items", []))
            compacted["skills"]["groups"] = trimmed_groups

    kept_bullet_ids: set[str] = set()
    for bullet in compacted.get("summary", []):
        bullet_id = bullet.get("bullet_id")
        if isinstance(bullet_id, str):
            kept_bullet_ids.add(bullet_id)
    for role in compacted.get("experience", []):
        for bullet in role.get("bullets", []):
            bullet_id = bullet.get("bullet_id")
            if isinstance(bullet_id, str):
                kept_bullet_ids.add(bullet_id)

    traceability = compacted.get("traceability", [])
    if isinstance(traceability, list):
        compacted["traceability"] = [
            entry
            for entry in traceability
            if isinstance(entry, dict) and entry.get("bullet_id") in kept_bullet_ids
        ]

    return compacted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate resume.json, resume.md, and optional resume.pdf."
    )
    parser.add_argument(
        "--input-model",
        required=True,
        help="Path to resume model JSON.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write generated artifacts.",
    )
    parser.add_argument(
        "--page-budget",
        type=int,
        choices=(1, 2),
        default=2,
        help="Override page budget (default: 2).",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Skip PDF generation.",
    )
    parser.add_argument(
        "--pdf-engine",
        default=None,
        help="Pandoc PDF engine (optional).",
    )
    args = parser.parse_args()

    input_model_path = Path(args.input_model)
    if not input_model_path.exists():
        print(f"ERROR: input model not found: {input_model_path}")
        return 1

    try:
        model = _load_model(input_model_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    model = _apply_budget_compaction(model, args.page_budget)
    errors = validate_model(model)
    if errors:
        print("ERROR: resume model validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / "resume.json"
    output_md = output_dir / "resume.md"
    output_pdf = output_dir / "resume.pdf"

    output_json.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(model)
    output_md.write_text(markdown, encoding="utf-8")

    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")

    if args.skip_pdf:
        print("Skipped PDF export (--skip-pdf set).")
        return 0

    try:
        export_markdown_to_pdf(
            input_md=output_md,
            output_pdf=output_pdf,
            page_budget=args.page_budget,
            pdf_engine=args.pdf_engine,
        )
    except RuntimeError as exc:
        print(f"ERROR: PDF export failed: {exc}")
        print("Artifacts generated: resume.json and resume.md")
        return 1

    print(f"Wrote {output_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
