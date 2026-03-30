from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from metadata_ontology import (  # noqa: E402
    load_tag_ontology,
    normalize_structured_metadata,
    validate_structured_metadata_against_ontology,
)


class MetadataOntologyTests(unittest.TestCase):
    def test_normalization_lowercases_snake_cases_and_dedupes(self) -> None:
        ontology, warnings = load_tag_ontology()
        self.assertIsNotNone(ontology)
        self.assertEqual(warnings, [])

        normalized, normalization_warnings = normalize_structured_metadata(
            {
                "technology_tags": ["LIME", "occlusion maps", "LIME"],
                "capability_tags": ["XAI", "model interpretability"],
            },
            ontology=ontology,
        )

        self.assertEqual(normalized["technology_tags"], ["lime", "occlusion_maps"])
        self.assertEqual(normalized["capability_tags"], ["model_interpretability", "xai"])
        self.assertTrue(normalization_warnings)

    def test_ontology_validation_warns_and_suggests_parent_tags(self) -> None:
        ontology, _warnings = load_tag_ontology()
        self.assertIsNotNone(ontology)

        warnings = validate_structured_metadata_against_ontology(
            {
                "technology_tags": ["lime"],
                "capability_tags": ["xai"],
                "domain_tags": ["education"],
                "role_family_tags": ["data_scientist"],
            },
            ontology=ontology,
        )

        self.assertTrue(
            any("model_interpretability" in warning for warning in warnings),
            msg=warnings,
        )

    def test_unknown_tags_get_close_match_warning(self) -> None:
        ontology, _warnings = load_tag_ontology()
        self.assertIsNotNone(ontology)

        warnings = validate_structured_metadata_against_ontology(
            {
                "technology_tags": ["lme"],
                "capability_tags": ["xai"],
                "domain_tags": ["education"],
                "role_family_tags": ["data_science"],
            },
            ontology=ontology,
        )

        self.assertTrue(any("Did you mean 'lime'" in warning for warning in warnings), msg=warnings)
        self.assertTrue(
            any("Did you mean 'data_scientist'" in warning for warning in warnings),
            msg=warnings,
        )


if __name__ == "__main__":
    unittest.main()
