#!/usr/bin/env python3
"""Render ATS-safe markdown resume from a validated resume model JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_resume_model import validate_model


def _contact_line(basics: dict) -> str:
    parts = [
        basics["email"],
        basics["phone"],
        basics["location"],
    ]
    links = basics.get("links", [])
    for link in links:
        parts.append(f"{link['label']}: {link['url']}")
    return " | ".join(parts)


def render_markdown(model: dict) -> str:
    lines: list[str] = []
    basics = model["basics"]

    lines.append(f"# {basics['name']}")
    lines.append("")
    lines.append(_contact_line(basics))
    lines.append("")

    summary = model.get("summary", [])
    if summary:
        lines.append("## Summary")
        lines.append("")
        for item in summary:
            lines.append(f"- {item['text']}")
        lines.append("")

    experience = model.get("experience", [])
    if experience:
        lines.append("## Experience")
        lines.append("")
        for role in experience:
            role_header = f"### {role['title']} | {role['company']}"
            if role.get("location"):
                role_header += f" | {role['location']}"
            lines.append(role_header)
            lines.append("")
            lines.append(f"{role['start_date']} - {role['end_date']}")
            lines.append("")
            for bullet in role.get("bullets", []):
                lines.append(f"- {bullet['text']}")
            lines.append("")

    skills = model.get("skills", {})
    groups = skills.get("groups", [])
    if groups:
        lines.append("## Skills")
        lines.append("")
        for group in groups:
            items = ", ".join(group["items"])
            lines.append(f"- **{group['name']}:** {items}")
        lines.append("")

    education = model.get("education", [])
    if education:
        lines.append("## Education")
        lines.append("")
        for item in education:
            education_line = f"- **{item['institution']}** | {item['degree']}"
            if item.get("location"):
                education_line += f" | {item['location']}"
            if item.get("graduation"):
                education_line += f" | {item['graduation']}"
            lines.append(education_line)
        lines.append("")

    gaps = model.get("gaps", [])
    if gaps:
        lines.append("## Gaps")
        lines.append("")
        for gap in gaps:
            lines.append(f"- {gap}")
        lines.append("")

    lines.append("## Traceability Map")
    lines.append("")
    for entry in model.get("traceability", []):
        story_ids = ", ".join(entry["story_ids"])
        lines.append(f"- `{entry['bullet_id']}` -> {story_ids}")
    lines.append("")

    return "\n".join(lines)


def _load_model(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Resume model root must be a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Render markdown resume from JSON model.")
    parser.add_argument("--input", required=True, help="Path to resume model JSON.")
    parser.add_argument("--output", required=True, help="Path to output markdown file.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        return 1

    try:
        model = _load_model(input_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    errors = validate_model(model)
    if errors:
        print("ERROR: model validation failed before rendering")
        for error in errors:
            print(f"- {error}")
        return 1

    markdown = render_markdown(model)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Rendered markdown resume: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
