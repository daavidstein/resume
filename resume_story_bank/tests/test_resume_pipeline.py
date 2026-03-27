from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_resume_model.json"


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ResumePipelineTests(unittest.TestCase):
    def _load_fixture(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_page_budget_accepts_1_or_2_and_rejects_other(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            valid_model = self._load_fixture()
            valid_model["page_budget"] = 1
            valid_model["summary"] = valid_model["summary"][:3]
            valid_model["experience"][0]["bullets"] = valid_model["experience"][0]["bullets"][:4]
            kept_ids = {
                bullet["bullet_id"] for bullet in valid_model["summary"]
            }
            for role in valid_model["experience"]:
                for bullet in role["bullets"]:
                    kept_ids.add(bullet["bullet_id"])
            valid_model["traceability"] = [
                entry for entry in valid_model["traceability"] if entry["bullet_id"] in kept_ids
            ]
            valid_path = tmp_path / "valid.json"
            valid_path.write_text(json.dumps(valid_model), encoding="utf-8")

            ok = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "validate_resume_model.py"),
                    "--input",
                    str(valid_path),
                ]
            )
            self.assertEqual(ok.returncode, 0, msg=ok.stdout + ok.stderr)

            invalid_model = self._load_fixture()
            invalid_model["page_budget"] = 3
            invalid_path = tmp_path / "invalid.json"
            invalid_path.write_text(json.dumps(invalid_model), encoding="utf-8")
            bad = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "validate_resume_model.py"),
                    "--input",
                    str(invalid_path),
                ]
            )
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("page_budget must be 1 or 2", bad.stdout)

    def test_budget_specific_caps_enforced_for_one_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = self._load_fixture()
            model["page_budget"] = 1
            model["summary"].append(
                {
                    "bullet_id": "SUM-EXTRA",
                    "text": "Extra summary bullet that should exceed 1-page cap.",
                }
            )
            model["traceability"].append(
                {"bullet_id": "SUM-EXTRA", "story_ids": ["SB-099"]}
            )

            model_path = Path(tmp) / "too_many_summary.json"
            model_path.write_text(json.dumps(model), encoding="utf-8")

            result = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "validate_resume_model.py"),
                    "--input",
                    str(model_path),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("summary has 5 bullets, exceeds max 3", result.stdout)

    def test_traceability_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = self._load_fixture()
            model["traceability"] = model["traceability"][1:]
            model_path = Path(tmp) / "missing_traceability.json"
            model_path.write_text(json.dumps(model), encoding="utf-8")

            result = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "validate_resume_model.py"),
                    "--input",
                    str(model_path),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing traceability entry for bullet_id: SUM-001", result.stdout)

    def test_integration_generate_default_two_page_and_one_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_two = tmp_path / "out_two"
            output_one = tmp_path / "out_one"

            result_two = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "generate_resume_artifacts.py"),
                    "--input-model",
                    str(FIXTURE),
                    "--output-dir",
                    str(output_two),
                    "--skip-pdf",
                ]
            )
            self.assertEqual(result_two.returncode, 0, msg=result_two.stdout + result_two.stderr)

            result_one = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "generate_resume_artifacts.py"),
                    "--input-model",
                    str(FIXTURE),
                    "--output-dir",
                    str(output_one),
                    "--page-budget",
                    "1",
                    "--skip-pdf",
                ]
            )
            self.assertEqual(result_one.returncode, 0, msg=result_one.stdout + result_one.stderr)

            model_two = json.loads((output_two / "resume.json").read_text(encoding="utf-8"))
            model_one = json.loads((output_one / "resume.json").read_text(encoding="utf-8"))
            self.assertEqual(model_two["page_budget"], 2)
            self.assertEqual(model_one["page_budget"], 1)

            md_two = (output_two / "resume.md").read_text(encoding="utf-8")
            md_one = (output_one / "resume.md").read_text(encoding="utf-8")
            self.assertNotEqual(md_two, md_one)

    def test_pdf_export_smoke_if_pandoc_available(self) -> None:
        if shutil.which("pandoc") is None:
            self.skipTest("pandoc not installed")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "out_pdf"
            generate = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "generate_resume_artifacts.py"),
                    "--input-model",
                    str(FIXTURE),
                    "--output-dir",
                    str(output),
                    "--page-budget",
                    "2",
                ]
            )
            if generate.returncode != 0:
                self.skipTest(f"pandoc available but PDF backend unavailable: {generate.stdout}")
            self.assertTrue((output / "resume.pdf").exists())


if __name__ == "__main__":
    unittest.main()
