from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from historical_resume_pipeline import (  # noqa: E402
    build_story_coverage_report,
    extract_historical_bullet_inventory,
    generate_candidate_bullet_batch,
    link_historical_bullets,
    normalize_pdf_text,
)


BASE_RESUME_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_base_resume.md"
STORY_BANK_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_story_bank.md"
JD_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_job_description.md"
REAL_RESUME_PDF = REPO_ROOT / "resumes" / "tailored" / "medium" / "resume.pdf"


class HistoricalResumePipelineTests(unittest.TestCase):
    def test_markdown_ingestion_extracts_summary_and_experience_bullets(self) -> None:
        inventory = extract_historical_bullet_inventory([BASE_RESUME_FIXTURE])
        self.assertEqual(inventory["artifact_type"], "historical_bullet_inventory")
        self.assertEqual(len(inventory["source_resumes"]), 1)
        sections = {item["section"] for item in inventory["bullets"]}
        self.assertIn("summary", sections)
        self.assertIn("experience", sections)
        self.assertTrue(any(item["role_title"] == "Senior ML Engineer" for item in inventory["bullets"]))

    def test_pdf_text_normalization_handles_bullets_and_wraps(self) -> None:
        raw = "Summary\n• First line\ncontinued line\n\n2\n• Second bullet\n"
        normalized = normalize_pdf_text(raw)
        self.assertIn("- First line continued line", normalized)
        self.assertIn("- Second bullet", normalized)
        self.assertNotIn("\n2\n", normalized)

    def test_pdf_ingestion_smoke_on_real_resume(self) -> None:
        if shutil.which("pdftotext") is None:
            self.skipTest("pdftotext not installed")
        inventory = extract_historical_bullet_inventory([REAL_RESUME_PDF])
        self.assertEqual(inventory["source_resumes"][0]["file_type"], "pdf")
        self.assertEqual(inventory["source_resumes"][0]["ingest_method"], "pdftotext")
        self.assertGreater(inventory["source_resumes"][0]["page_count"], 0)
        self.assertGreater(len(inventory["bullets"]), 0)

    def test_linking_populates_candidate_story_links_and_confidence(self) -> None:
        inventory = extract_historical_bullet_inventory([BASE_RESUME_FIXTURE])
        stories_text = STORY_BANK_FIXTURE.read_text(encoding="utf-8")
        from historical_resume_pipeline import load_story_bank  # noqa: E402

        with tempfile.TemporaryDirectory() as tmp:
            story_path = Path(tmp) / "story_bank.md"
            story_path.write_text(stories_text, encoding="utf-8")
            stories = load_story_bank(story_path)
        linked = link_historical_bullets(inventory, stories)
        self.assertTrue(any(item["candidate_story_links"] for item in linked["bullets"]))
        self.assertTrue(any(item["link_confidence"] != "unlinked" for item in linked["bullets"]))

    def test_coverage_report_includes_expected_statuses(self) -> None:
        inventory = {
            "bullets": [
                {
                    "historical_bullet_id": "HB-001",
                    "text": "Built PyTorch models and deployed monitored services in AWS.",
                    "linked_story_ids": ["SB-101"],
                    "link_confidence": "strong",
                },
                {
                    "historical_bullet_id": "HB-002",
                    "text": "Ran A/B tests and partnered with product managers.",
                    "linked_story_ids": ["SB-102"],
                    "link_confidence": "partial",
                },
            ]
        }
        from historical_resume_pipeline import load_story_bank  # noqa: E402

        with tempfile.TemporaryDirectory() as tmp:
            story_path = Path(tmp) / "story_bank.md"
            story_path.write_text(STORY_BANK_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
            stories = load_story_bank(story_path)
        report = build_story_coverage_report(inventory, stories)
        statuses = {row["story_id"]: row["coverage_status"] for row in report["stories"]}
        self.assertEqual(statuses["SB-101"], "well_represented")
        self.assertEqual(statuses["SB-102"], "partially_represented")

    def test_candidate_generation_prefers_reuse_then_adaptation_then_synthesis(self) -> None:
        from historical_resume_pipeline import load_story_bank  # noqa: E402

        story_text = STORY_BANK_FIXTURE.read_text(encoding="utf-8") + """

## Story: Monitoring and Reliability

### Story ID
SB-103

### Context
Built reliability guardrails.

### Actions
- Added monitoring and testing workflows.

### Outcomes
- Improved reliability.

### Skills/Keywords
monitoring, testing

### Source References
notes
"""
        with tempfile.TemporaryDirectory() as tmp:
            story_path = Path(tmp) / "story_bank.md"
            story_path.write_text(story_text, encoding="utf-8")
            stories = load_story_bank(story_path)

        linked_inventory = {
            "bullets": [
                {
                    "historical_bullet_id": "HB-001",
                    "text": "Built PyTorch models and deployed monitored services in AWS.",
                    "linked_story_ids": ["SB-101"],
                    "link_confidence": "strong",
                },
                {
                    "historical_bullet_id": "HB-002",
                    "text": "Ran A/B tests and partnered with product managers.",
                    "linked_story_ids": ["SB-102"],
                    "link_confidence": "partial",
                },
            ]
        }
        batch = generate_candidate_bullet_batch(
            linked_inventory,
            stories,
            jd_text=JD_FIXTURE.read_text(encoding="utf-8"),
        )
        by_story = {tuple(item["source_story_ids"]): item for item in batch["bullets"]}
        self.assertEqual(by_story[("SB-101",)]["origin_mode"], "historical_reuse")
        self.assertEqual(by_story[("SB-102",)]["origin_mode"], "historical_adaptation")
        self.assertEqual(by_story[("SB-103",)]["origin_mode"], "story_synthesis")
        for item in batch["bullets"]:
            self.assertIn("coverage_reason", item)
            self.assertIn("review", item)
            self.assertEqual(item["review"], {"label": "", "notes": ""})

    def test_cli_end_to_end_writes_expected_artifacts(self) -> None:
        if shutil.which("pdftotext") is None:
            self.skipTest("pdftotext not installed")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            inventory_path = tmp_path / "inventory.json"
            linked_path = tmp_path / "linked.json"
            coverage_path = tmp_path / "coverage.json"
            candidates_path = tmp_path / "candidates.json"

            commands = [
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_historical_resumes.py"),
                    "--resume",
                    str(BASE_RESUME_FIXTURE),
                    "--resume",
                    str(REAL_RESUME_PDF),
                    "--output",
                    str(inventory_path),
                    "--format",
                    "both",
                ],
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "link_historical_bullets.py"),
                    "--historical-bullets",
                    str(inventory_path),
                    "--master-story-bank",
                    str(STORY_BANK_FIXTURE),
                    "--output",
                    str(linked_path),
                    "--format",
                    "both",
                ],
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "report_story_coverage.py"),
                    "--linked-historical-bullets",
                    str(linked_path),
                    "--master-story-bank",
                    str(STORY_BANK_FIXTURE),
                    "--output",
                    str(coverage_path),
                    "--format",
                    "both",
                ],
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_candidate_bullets.py"),
                    "--linked-historical-bullets",
                    str(linked_path),
                    "--master-story-bank",
                    str(STORY_BANK_FIXTURE),
                    "--job-description",
                    str(JD_FIXTURE),
                    "--output",
                    str(candidates_path),
                    "--format",
                    "both",
                ],
            ]
            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            for path in [
                inventory_path,
                inventory_path.with_suffix(".md"),
                linked_path,
                linked_path.with_suffix(".md"),
                coverage_path,
                coverage_path.with_suffix(".md"),
                candidates_path,
                candidates_path.with_suffix(".md"),
            ]:
                self.assertTrue(path.exists(), msg=f"Missing artifact: {path}")

            data = json.loads(candidates_path.read_text(encoding="utf-8"))
            self.assertEqual(data["artifact_type"], "candidate_bullet_batch")
            self.assertTrue(data["bullets"])


if __name__ == "__main__":
    unittest.main()
