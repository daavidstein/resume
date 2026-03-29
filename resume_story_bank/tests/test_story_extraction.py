from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from extract_story_candidates import (
    _next_story_id,
    extract_story_candidates,
    render_story_candidates_markdown,
)


TRANSCRIPT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_transcript.md"
STORY_BANK_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_story_bank.md"


class StoryExtractionTests(unittest.TestCase):
    def test_next_story_id_uses_max_plus_one(self) -> None:
        master_text = STORY_BANK_FIXTURE.read_text(encoding="utf-8")
        self.assertEqual(_next_story_id(master_text), 103)

    def test_extract_story_candidates_returns_ranked_candidates(self) -> None:
        transcript = TRANSCRIPT_FIXTURE.read_text(encoding="utf-8")
        stories = extract_story_candidates(
            transcript_text=transcript,
            source_reference=str(TRANSCRIPT_FIXTURE),
            existing_master_story_bank_text=STORY_BANK_FIXTURE.read_text(encoding="utf-8"),
            max_stories=3,
        )
        self.assertGreaterEqual(len(stories), 1)
        first = stories[0]
        self.assertTrue(first.action)
        self.assertGreaterEqual(first.source_line, 1)
        self.assertIn(str(TRANSCRIPT_FIXTURE), first.source_reference)

    def test_render_story_candidates_markdown_contains_required_sections(self) -> None:
        transcript = TRANSCRIPT_FIXTURE.read_text(encoding="utf-8")
        stories = extract_story_candidates(
            transcript_text=transcript,
            source_reference=str(TRANSCRIPT_FIXTURE),
            existing_master_story_bank_text="",
            max_stories=2,
        )
        markdown = render_story_candidates_markdown(stories=stories, starting_story_number=120)
        self.assertIn("## Candidate Story Entries", markdown)
        self.assertIn("### Story ID", markdown)
        self.assertIn("### Context", markdown)
        self.assertIn("### Actions", markdown)
        self.assertIn("### Outcomes", markdown)
        self.assertIn("### Skills/Keywords", markdown)
        self.assertIn("### Source References", markdown)
        self.assertIn("## Mapping Notes", markdown)
        self.assertIn("## Open Questions", markdown)
        self.assertIn("SB-120", markdown)

    def test_cli_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "candidate_stories.md"
            script_path = REPO_ROOT / "scripts" / "extract_story_candidates.py"
            result = subprocess.run(
                [
                    "python3",
                    str(script_path),
                    "--input",
                    str(TRANSCRIPT_FIXTURE),
                    "--master-story-bank",
                    str(STORY_BANK_FIXTURE),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(output_path.exists())
            out = output_path.read_text(encoding="utf-8")
            self.assertIn("## Candidate Story Entries", out)


if __name__ == "__main__":
    unittest.main()
