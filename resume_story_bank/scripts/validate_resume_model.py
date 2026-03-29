#!/usr/bin/env python3
"""Validate a structured resume model used for markdown/PDF rendering.

Maintainer note:
- Keep this script standard-library-only for now.
- If schema complexity keeps growing (more nested structures, conditional fields,
  or harder-to-maintain cross-field rules), consider migrating shape/type
  validation to Pydantic and keeping only business-specific checks here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


STORY_ID_PATTERN = re.compile(r"^SB-\d{3,}$")
VALID_PAGE_BUDGETS = {1, 2}

BUDGET_LIMITS = {
    1: {
        "summary_bullets_max": 3,
        "experience_roles_max": 4,
        "experience_bullets_per_role_max": 4,
        "skills_groups_max": 4,
        "skills_items_total_max": 20,
    },
    2: {
        "summary_bullets_max": 4,
        "experience_roles_max": 6,
        "experience_bullets_per_role_max": 6,
        "skills_groups_max": 6,
        "skills_items_total_max": 32,
    },
}


def _expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validate_non_empty_string(value: object, field: str, errors: list[str]) -> None:
    _expect(isinstance(value, str) and value.strip(), f"{field} must be a non-empty string", errors)


def _validate_bullets(
    bullets: object,
    field: str,
    errors: list[str],
    required: bool = True,
) -> list[str]:
    bullet_ids: list[str] = []
    if bullets is None:
        if required:
            errors.append(f"{field} is required")
        return bullet_ids

    if not isinstance(bullets, list):
        errors.append(f"{field} must be an array")
        return bullet_ids

    for idx, bullet in enumerate(bullets):
        prefix = f"{field}[{idx}]"
        if not isinstance(bullet, dict):
            errors.append(f"{prefix} must be an object")
            continue
        bullet_id = bullet.get("bullet_id")
        text = bullet.get("text")
        _validate_non_empty_string(bullet_id, f"{prefix}.bullet_id", errors)
        _validate_non_empty_string(text, f"{prefix}.text", errors)
        if isinstance(bullet_id, str) and bullet_id.strip():
            bullet_ids.append(bullet_id.strip())
    return bullet_ids


def validate_model(model: dict) -> list[str]:
    errors: list[str] = []

    page_budget = model.get("page_budget")
    _expect(page_budget in VALID_PAGE_BUDGETS, "page_budget must be 1 or 2", errors)
    if page_budget not in VALID_PAGE_BUDGETS:
        return errors

    limits = BUDGET_LIMITS[page_budget]

    basics = model.get("basics")
    _expect(isinstance(basics, dict), "basics must be an object", errors)
    if isinstance(basics, dict):
        _validate_non_empty_string(basics.get("name"), "basics.name", errors)
        _validate_non_empty_string(basics.get("email"), "basics.email", errors)
        _validate_non_empty_string(basics.get("phone"), "basics.phone", errors)
        _validate_non_empty_string(basics.get("location"), "basics.location", errors)
        links = basics.get("links", [])
        _expect(isinstance(links, list), "basics.links must be an array", errors)
        if isinstance(links, list):
            for idx, link in enumerate(links):
                prefix = f"basics.links[{idx}]"
                _expect(isinstance(link, dict), f"{prefix} must be an object", errors)
                if isinstance(link, dict):
                    _validate_non_empty_string(link.get("label"), f"{prefix}.label", errors)
                    _validate_non_empty_string(link.get("url"), f"{prefix}.url", errors)

    summary_ids = _validate_bullets(model.get("summary"), "summary", errors, required=True)
    _expect(
        len(summary_ids) <= limits["summary_bullets_max"],
        (
            f"summary has {len(summary_ids)} bullets, exceeds max "
            f"{limits['summary_bullets_max']} for page_budget={page_budget}"
        ),
        errors,
    )

    experience = model.get("experience")
    experience_ids: list[str] = []
    _expect(isinstance(experience, list), "experience must be an array", errors)
    if isinstance(experience, list):
        _expect(
            len(experience) <= limits["experience_roles_max"],
            (
                f"experience has {len(experience)} roles, exceeds max "
                f"{limits['experience_roles_max']} for page_budget={page_budget}"
            ),
            errors,
        )
        for idx, role in enumerate(experience):
            prefix = f"experience[{idx}]"
            _expect(isinstance(role, dict), f"{prefix} must be an object", errors)
            if not isinstance(role, dict):
                continue
            _validate_non_empty_string(role.get("title"), f"{prefix}.title", errors)
            _validate_non_empty_string(role.get("company"), f"{prefix}.company", errors)
            _validate_non_empty_string(role.get("start_date"), f"{prefix}.start_date", errors)
            _validate_non_empty_string(role.get("end_date"), f"{prefix}.end_date", errors)

            role_bullets = _validate_bullets(role.get("bullets"), f"{prefix}.bullets", errors, required=True)
            _expect(
                len(role_bullets) <= limits["experience_bullets_per_role_max"],
                (
                    f"{prefix}.bullets has {len(role_bullets)} entries, exceeds max "
                    f"{limits['experience_bullets_per_role_max']} for page_budget={page_budget}"
                ),
                errors,
            )
            experience_ids.extend(role_bullets)

    skills = model.get("skills")
    _expect(isinstance(skills, dict), "skills must be an object", errors)
    if isinstance(skills, dict):
        groups = skills.get("groups", [])
        _expect(isinstance(groups, list), "skills.groups must be an array", errors)
        total_items = 0
        if isinstance(groups, list):
            _expect(
                len(groups) <= limits["skills_groups_max"],
                (
                    f"skills.groups has {len(groups)} entries, exceeds max "
                    f"{limits['skills_groups_max']} for page_budget={page_budget}"
                ),
                errors,
            )
            for idx, group in enumerate(groups):
                prefix = f"skills.groups[{idx}]"
                _expect(isinstance(group, dict), f"{prefix} must be an object", errors)
                if not isinstance(group, dict):
                    continue
                _validate_non_empty_string(group.get("name"), f"{prefix}.name", errors)
                items = group.get("items", [])
                _expect(isinstance(items, list), f"{prefix}.items must be an array", errors)
                if isinstance(items, list):
                    total_items += len(items)
                    for item_idx, item in enumerate(items):
                        _validate_non_empty_string(item, f"{prefix}.items[{item_idx}]", errors)
        _expect(
            total_items <= limits["skills_items_total_max"],
            (
                f"skills has {total_items} total items, exceeds max "
                f"{limits['skills_items_total_max']} for page_budget={page_budget}"
            ),
            errors,
        )

    education = model.get("education", [])
    _expect(isinstance(education, list), "education must be an array", errors)
    if isinstance(education, list):
        for idx, item in enumerate(education):
            prefix = f"education[{idx}]"
            _expect(isinstance(item, dict), f"{prefix} must be an object", errors)
            if isinstance(item, dict):
                _validate_non_empty_string(item.get("institution"), f"{prefix}.institution", errors)
                _validate_non_empty_string(item.get("degree"), f"{prefix}.degree", errors)
                _validate_non_empty_string(item.get("start_date"), f"{prefix}.start_date", errors)
                _validate_non_empty_string(item.get("end_date"), f"{prefix}.end_date", errors)

    gaps = model.get("gaps", [])
    _expect(isinstance(gaps, list), "gaps must be an array", errors)
    if isinstance(gaps, list):
        for idx, gap in enumerate(gaps):
            _validate_non_empty_string(gap, f"gaps[{idx}]", errors)

    traceability = model.get("traceability")
    _expect(isinstance(traceability, list), "traceability must be an array", errors)
    traceability_map: dict[str, list[str]] = {}
    if isinstance(traceability, list):
        for idx, entry in enumerate(traceability):
            prefix = f"traceability[{idx}]"
            _expect(isinstance(entry, dict), f"{prefix} must be an object", errors)
            if not isinstance(entry, dict):
                continue
            bullet_id = entry.get("bullet_id")
            _validate_non_empty_string(bullet_id, f"{prefix}.bullet_id", errors)
            story_ids = entry.get("story_ids")
            _expect(isinstance(story_ids, list) and len(story_ids) > 0, f"{prefix}.story_ids must be a non-empty array", errors)
            clean_story_ids: list[str] = []
            if isinstance(story_ids, list):
                for sid_idx, story_id in enumerate(story_ids):
                    _validate_non_empty_string(story_id, f"{prefix}.story_ids[{sid_idx}]", errors)
                    if isinstance(story_id, str):
                        clean_story_ids.append(story_id)
                        if not STORY_ID_PATTERN.match(story_id):
                            errors.append(f"{prefix}.story_ids[{sid_idx}] has invalid ID format: {story_id}")
            if isinstance(bullet_id, str) and bullet_id.strip():
                traceability_map[bullet_id.strip()] = clean_story_ids

    all_bullet_ids = summary_ids + experience_ids
    duplicate_ids = {bid for bid in all_bullet_ids if all_bullet_ids.count(bid) > 1}
    for duplicate in sorted(duplicate_ids):
        errors.append(f"Duplicate bullet_id detected: {duplicate}")

    for bullet_id in all_bullet_ids:
        story_ids = traceability_map.get(bullet_id)
        if not story_ids:
            errors.append(f"Missing traceability entry for bullet_id: {bullet_id}")

    for bullet_id in traceability_map:
        if bullet_id not in all_bullet_ids:
            errors.append(f"Traceability bullet_id not present in summary/experience: {bullet_id}")

    return errors


def load_story_ids_from_master_story_bank(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    ids: set[str] = set()
    for match in re.finditer(r"(?m)^### Story ID\s*$\n+([^\n]+)\s*$", text):
        story_id = match.group(1).strip()
        if STORY_ID_PATTERN.match(story_id):
            ids.add(story_id)
    return ids


def validate_traceability_story_ids(model: dict, valid_story_ids: set[str]) -> list[str]:
    errors: list[str] = []
    traceability = model.get("traceability", [])
    if not isinstance(traceability, list):
        return errors

    for idx, entry in enumerate(traceability):
        if not isinstance(entry, dict):
            continue
        story_ids = entry.get("story_ids", [])
        if not isinstance(story_ids, list):
            continue
        for sid_idx, story_id in enumerate(story_ids):
            if isinstance(story_id, str) and story_id not in valid_story_ids:
                errors.append(
                    f"traceability[{idx}].story_ids[{sid_idx}] references unknown story ID: {story_id}"
                )
    return errors


def _load_model(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Resume model root must be a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate resume model JSON.")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to resume model JSON.",
    )
    parser.add_argument(
        "--master-story-bank",
        default=None,
        help="Optional path to master story bank markdown for strict story-ID existence checks.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        return 1

    try:
        model = _load_model(input_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    errors = validate_model(model)
    if args.master_story_bank:
        story_bank_path = Path(args.master_story_bank)
        if not story_bank_path.exists():
            print(f"ERROR: master story bank not found: {story_bank_path}")
            return 1
        valid_story_ids = load_story_ids_from_master_story_bank(story_bank_path)
        if not valid_story_ids:
            print(f"ERROR: no valid story IDs found in master story bank: {story_bank_path}")
            return 1
        errors.extend(validate_traceability_story_ids(model, valid_story_ids))

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"VALIDATION PASSED: {input_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
