from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_resume_model.json"
BASE_RESUME_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_base_resume.md"
JD_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_job_description.md"
JD_TXT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_job_description.txt"
JD_HTML_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_job_description.html"
STORY_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_story_bank.md"


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # Keep tests deterministic/offline regardless of caller shell env.
    env.pop("RESUME_SB_EMBEDDING_BACKEND", None)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
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
            self.assertNotIn("## Gaps", md_two)
            self.assertNotIn("## Traceability Map", md_two)
            self.assertNotIn("SB-", md_two)
            self.assertNotIn("## Gaps", md_one)
            self.assertNotIn("## Traceability Map", md_one)
            self.assertNotIn("SB-", md_one)

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

    def test_include_internal_generates_internal_markdown_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out_internal"
            result = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "generate_resume_artifacts.py"),
                    "--input-model",
                    str(FIXTURE),
                    "--output-dir",
                    str(output_dir),
                    "--include-internal",
                    "--skip-pdf",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            public_md = (output_dir / "resume.md").read_text(encoding="utf-8")
            internal_md = (output_dir / "resume_internal.md").read_text(encoding="utf-8")
            self.assertNotIn("## Gaps", public_md)
            self.assertNotIn("## Traceability Map", public_md)
            self.assertIn("## Gaps", internal_md)
            self.assertIn("## Traceability Map", internal_md)

    def test_tailor_resume_model_generates_valid_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jd_variants = [JD_FIXTURE, JD_TXT_FIXTURE, JD_HTML_FIXTURE]
            cache_path = Path(tmp) / "embeddings_cache.json"
            for idx, jd_path in enumerate(jd_variants, start=1):
                output_path = Path(tmp) / f"tailored_{idx}.json"
                result = _run(
                    [
                        "python3",
                        str(SCRIPTS_DIR / "tailor_resume_model.py"),
                        "--base-resume",
                        str(BASE_RESUME_FIXTURE),
                        "--job-description",
                        str(jd_path),
                        "--master-story-bank",
                        str(STORY_FIXTURE),
                        "--embedding-cache",
                        str(cache_path),
                        "--output",
                        str(output_path),
                        "--page-budget",
                        "2",
                    ]
                )
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertTrue(output_path.exists())

                validate = _run(
                    [
                        "python3",
                        str(SCRIPTS_DIR / "validate_resume_model.py"),
                        "--input",
                        str(output_path),
                    ]
                )
                self.assertEqual(validate.returncode, 0, msg=validate.stdout + validate.stderr)

    def test_tailor_resume_model_supports_job_description_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "tailored_from_url.json"
            jd_url = JD_HTML_FIXTURE.resolve().as_uri()
            cache_path = Path(tmp) / "embeddings_cache.json"
            jd_fetch_cache_dir = Path(tmp) / "jd_fetch_cache"
            result = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "tailor_resume_model.py"),
                    "--base-resume",
                    str(BASE_RESUME_FIXTURE),
                    "--job-description-url",
                    jd_url,
                    "--master-story-bank",
                    str(STORY_FIXTURE),
                    "--embedding-cache",
                    str(cache_path),
                    "--jd-fetch-cache-dir",
                    str(jd_fetch_cache_dir),
                    "--output",
                    str(output_path),
                    "--page-budget",
                    "2",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(output_path.exists())
            metadata_files = list(jd_fetch_cache_dir.glob("*.json"))
            artifact_files = list(jd_fetch_cache_dir.glob("*.html"))
            self.assertEqual(len(metadata_files), 1)
            self.assertEqual(len(artifact_files), 1)
            metadata = json.loads(metadata_files[0].read_text(encoding="utf-8"))
            self.assertEqual(metadata["url"], jd_url)
            self.assertEqual(metadata["is_html"], True)
            self.assertEqual(Path(metadata["raw_path"]), artifact_files[0])
            self.assertEqual(Path(metadata["metadata_path"]), metadata_files[0])

    def test_tailor_resume_model_rejects_both_jd_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "invalid.json"
            jd_url = JD_HTML_FIXTURE.resolve().as_uri()
            result = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "tailor_resume_model.py"),
                    "--base-resume",
                    str(BASE_RESUME_FIXTURE),
                    "--job-description",
                    str(JD_FIXTURE),
                    "--job-description-url",
                    jd_url,
                    "--master-story-bank",
                    str(STORY_FIXTURE),
                    "--output",
                    str(output_path),
                ]
            )
            self.assertNotEqual(result.returncode, 0)

    def test_tailor_resume_model_honors_one_page_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "tailored_one_page.json"
            cache_path = Path(tmp) / "embeddings_cache.json"
            result = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "tailor_resume_model.py"),
                    "--base-resume",
                    str(BASE_RESUME_FIXTURE),
                    "--job-description",
                    str(JD_FIXTURE),
                    "--master-story-bank",
                    str(STORY_FIXTURE),
                    "--embedding-cache",
                    str(cache_path),
                    "--output",
                    str(output_path),
                    "--page-budget",
                    "1",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            model = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(model["page_budget"], 1)
            self.assertLessEqual(len(model["summary"]), 3)
            for role in model["experience"]:
                self.assertLessEqual(len(role["bullets"]), 4)

    def test_validate_resume_model_strict_story_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = self._load_fixture()
            model["traceability"][0]["story_ids"] = ["SB-999"]
            model_path = Path(tmp) / "bad_story_id.json"
            model_path.write_text(json.dumps(model), encoding="utf-8")

            result = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "validate_resume_model.py"),
                    "--input",
                    str(model_path),
                    "--master-story-bank",
                    str(STORY_FIXTURE),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("references unknown story ID: SB-999", result.stdout)

    def test_tailor_resume_model_preflight_requires_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_base = Path(tmp) / "bad_base.md"
            bad_base.write_text("# Name\n\nNo expected sections.\n", encoding="utf-8")
            output_path = Path(tmp) / "out.json"

            result = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "tailor_resume_model.py"),
                    "--base-resume",
                    str(bad_base),
                    "--job-description",
                    str(JD_FIXTURE),
                    "--master-story-bank",
                    str(STORY_FIXTURE),
                    "--embedding-cache",
                    str(Path(tmp) / "embeddings_cache.json"),
                    "--output",
                    str(output_path),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("base resume format preflight failed", result.stdout)

    def test_tailor_resume_model_uses_embedding_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "embeddings_cache.json"
            output_a = Path(tmp) / "a.json"
            output_b = Path(tmp) / "b.json"
            report_b = Path(tmp) / "selection_b.json"

            first = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "tailor_resume_model.py"),
                    "--base-resume",
                    str(BASE_RESUME_FIXTURE),
                    "--job-description",
                    str(JD_FIXTURE),
                    "--master-story-bank",
                    str(STORY_FIXTURE),
                    "--embedding-cache",
                    str(cache_path),
                    "--output",
                    str(output_a),
                    "--page-budget",
                    "2",
                ]
            )
            self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)
            self.assertTrue(cache_path.exists())

            second = _run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "tailor_resume_model.py"),
                    "--base-resume",
                    str(BASE_RESUME_FIXTURE),
                    "--job-description",
                    str(JD_FIXTURE),
                    "--master-story-bank",
                    str(STORY_FIXTURE),
                    "--embedding-cache",
                    str(cache_path),
                    "--selection-report",
                    str(report_b),
                    "--output",
                    str(output_b),
                    "--page-budget",
                    "2",
                ]
            )
            self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
            report = json.loads(report_b.read_text(encoding="utf-8"))
            self.assertIn("embedding_cache", report)
            self.assertGreater(report["embedding_cache"]["hits"], 0)

    def test_openai_backend_requires_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env.pop("OPENAI_API_KEY", None)
            env.pop("RESUME_SB_EMBEDDING_BACKEND", None)
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "tailor_resume_model.py"),
                    "--base-resume",
                    str(BASE_RESUME_FIXTURE),
                    "--job-description",
                    str(JD_FIXTURE),
                    "--master-story-bank",
                    str(STORY_FIXTURE),
                    "--embedding-backend",
                    "openai",
                    "--output",
                    str(Path(tmp) / "out.json"),
                ],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("OPENAI_API_KEY is required", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
