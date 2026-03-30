from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


Ontology = Dict[str, object]

ONTOLOGY_CONTROLLED_FIELDS = {
    "technology_tags",
    "capability_tags",
    "domain_tags",
    "role_family_tags",
}

NORMALIZABLE_LIST_FIELDS = ONTOLOGY_CONTROLLED_FIELDS | {
    "business_problem_tags",
    "audience_tags",
    "preferred_resume_angles",
    "wording_constraints",
    "caveats",
    "forbidden_claims",
}


def default_ontology_path() -> Path:
    return Path(__file__).resolve().parents[1] / "specs" / "tag_ontology.yaml"


def load_tag_ontology(path: Optional[Path] = None) -> Tuple[Optional[Ontology], List[str]]:
    ontology_path = path or default_ontology_path()
    warnings: List[str] = []
    if not ontology_path.exists():
        warnings.append(f"Tag ontology file not found: {ontology_path}")
        return None, warnings
    if yaml is None:
        warnings.append(
            "PyYAML is not installed; skipping ontology-backed metadata validation."
        )
        return None, warnings
    try:
        loaded = yaml.safe_load(ontology_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        warnings.append(f"Failed to load tag ontology from {ontology_path}: {exc}")
        return None, warnings
    if not isinstance(loaded, dict):
        warnings.append(f"Tag ontology has unexpected top-level shape: {ontology_path}")
        return None, warnings
    return loaded, warnings


def normalize_tag(tag: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", tag.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def normalize_structured_metadata(
    metadata: Dict[str, object],
    ontology: Optional[Ontology] = None,
) -> Tuple[Dict[str, object], List[str]]:
    warnings: List[str] = []
    normalized: Dict[str, object] = {}
    sort_tags = True
    if ontology:
        sort_tags = bool(ontology.get("normalization", {}).get("sort_tags", True))

    for key, value in metadata.items():
        if isinstance(value, list) and key in NORMALIZABLE_LIST_FIELDS:
            raw_tags = [item for item in value if isinstance(item, str)]
            normalized_tags = [normalize_tag(item) for item in raw_tags if normalize_tag(item)]
            if raw_tags != normalized_tags:
                warnings.append(
                    f"field '{key}' tags normalized to lowercase snake_case: {raw_tags} -> {normalized_tags}"
                )
            deduped_tags = sorted(set(normalized_tags)) if sort_tags else list(dict.fromkeys(normalized_tags))
            if normalized_tags != deduped_tags:
                warnings.append(
                    f"field '{key}' tags were deduped/sorted for comparison: {normalized_tags} -> {deduped_tags}"
                )
            normalized[key] = deduped_tags
        else:
            normalized[key] = value
    return normalized, warnings


def validate_structured_metadata_against_ontology(
    metadata: Dict[str, object],
    ontology: Optional[Ontology],
) -> List[str]:
    if ontology is None:
        return []

    warnings: List[str] = []
    allowed_tags = ontology.get("allowed_tags", {})
    parent_map = ontology.get("parent_map", {}).get("technology_tags", {})

    allowed_technology_tags = set(parent_map.keys())
    for field in ("capability_tags", "domain_tags", "role_family_tags"):
        known = set(allowed_tags.get(field, []))
        for tag in _get_tags(metadata, field):
            if tag not in known:
                suggestion = _closest_match(tag, known)
                suffix = f" Did you mean '{suggestion}'?" if suggestion else ""
                warnings.append(f"Unknown {field} tag '{tag}'.{suffix}")

    for tag in _get_tags(metadata, "technology_tags"):
        if tag not in allowed_technology_tags:
            suggestion = _closest_match(tag, allowed_technology_tags)
            suffix = f" Did you mean '{suggestion}'?" if suggestion else ""
            warnings.append(f"Unknown technology_tags tag '{tag}'.{suffix}")

    capability_tags = set(_get_tags(metadata, "capability_tags"))
    technology_tags = set(_get_tags(metadata, "technology_tags"))

    direct_parent_capabilities: Set[str] = set()
    reverse_parent_map: Dict[str, Set[str]] = {}
    allowed_capabilities = set(allowed_tags.get("capability_tags", []))

    for technology_tag, mapping in parent_map.items():
        capability_values = mapping.get("capability_tags", [])
        if not isinstance(capability_values, list):
            continue
        for capability_tag in capability_values:
            reverse_parent_map.setdefault(capability_tag, set()).add(technology_tag)
        if technology_tag not in technology_tags:
            continue
        for capability_tag in capability_values:
            if capability_tag not in allowed_capabilities:
                warnings.append(
                    f"Ontology maps technology_tags '{technology_tag}' to unsupported capability tag '{capability_tag}'. Expand ontology before auto-adding it."
                )
                continue
            direct_parent_capabilities.add(capability_tag)
            if capability_tag not in capability_tags:
                warnings.append(
                    f"technology_tags '{technology_tag}' supports immediate parent capability '{capability_tag}'. Consider adding it to capability_tags if directly evidenced."
                )

    for capability_tag in sorted(capability_tags):
        inferred_from = reverse_parent_map.get(capability_tag, set())
        if inferred_from and not (inferred_from & technology_tags):
            warnings.append(
                f"capability_tags '{capability_tag}' has no supporting technology_tags from ontology ({', '.join(sorted(inferred_from))}). Keep it only if separately evidenced."
            )
        if technology_tags and capability_tag in allowed_capabilities and capability_tag not in direct_parent_capabilities:
            if capability_tag in reverse_parent_map and not (reverse_parent_map[capability_tag] & technology_tags):
                warnings.append(
                    f"capability_tags '{capability_tag}' may reflect a broader abstraction than the present technology_tags support. Verify it is directly evidenced and not a multi-hop inference."
                )

    return warnings


def _get_tags(metadata: Dict[str, object], field: str) -> List[str]:
    value = metadata.get(field, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _closest_match(tag: str, candidates: Set[str]) -> Optional[str]:
    matches = difflib.get_close_matches(tag, sorted(candidates), n=1, cutoff=0.7)
    if matches:
        return matches[0]
    return None
