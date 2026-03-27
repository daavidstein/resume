#!/usr/bin/env python3
"""Export markdown resume to PDF via pandoc."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PAGE_PROFILES = {
    1: {
        "fontsize": "10pt",
        "geometry": "margin=0.55in",
    },
    2: {
        "fontsize": "11pt",
        "geometry": "margin=0.75in",
    },
}


def export_markdown_to_pdf(
    input_md: Path,
    output_pdf: Path,
    page_budget: int,
    pdf_engine: str | None = None,
) -> None:
    if page_budget not in PAGE_PROFILES:
        raise ValueError("page_budget must be 1 or 2")

    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc not found on PATH")

    profile = PAGE_PROFILES[page_budget]
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "pandoc",
        str(input_md),
        "--from",
        "markdown",
        "--to",
        "pdf",
        "-V",
        f"fontsize={profile['fontsize']}",
        "-V",
        f"geometry:{profile['geometry']}",
        "--standalone",
        "--output",
        str(output_pdf),
    ]
    if pdf_engine:
        command[6:6] = ["--pdf-engine", pdf_engine]

    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return

    stderr = proc.stderr.strip() or "unknown pandoc error"
    # Older pandoc builds (e.g. 2.5) do not accept "--to pdf".
    fallback_needed = "use -t latex" in stderr.lower() or "not compatible with output format pdf" in stderr.lower()
    if not fallback_needed:
        raise RuntimeError(f"pandoc failed: {stderr}")

    chosen_engine = pdf_engine
    if not chosen_engine:
        if shutil.which("xelatex"):
            chosen_engine = "xelatex"
        elif shutil.which("pdflatex"):
            chosen_engine = "pdflatex"
        else:
            raise RuntimeError(
                "pandoc fallback requires a TeX engine (xelatex or pdflatex) on PATH"
            )

    fallback_command = [
        "pandoc",
        str(input_md),
        "--from",
        "markdown",
        "--to",
        "latex",
        "--pdf-engine",
        chosen_engine,
        "-V",
        f"fontsize={profile['fontsize']}",
        "-V",
        f"geometry:{profile['geometry']}",
        "--standalone",
        "--output",
        str(output_pdf),
    ]
    fallback_proc = subprocess.run(
        fallback_command, capture_output=True, text=True, check=False
    )
    if fallback_proc.returncode != 0:
        fallback_stderr = fallback_proc.stderr.strip() or "unknown pandoc fallback error"
        raise RuntimeError(f"pandoc failed: {fallback_stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export markdown resume to PDF.")
    parser.add_argument("--input", required=True, help="Path to markdown resume.")
    parser.add_argument("--output", required=True, help="Path to output PDF.")
    parser.add_argument(
        "--page-budget",
        type=int,
        choices=(1, 2),
        default=2,
        help="Page budget profile (default: 2).",
    )
    parser.add_argument(
        "--pdf-engine",
        default=None,
        help="Pandoc PDF engine (optional).",
    )
    args = parser.parse_args()

    input_md = Path(args.input)
    output_pdf = Path(args.output)
    if not input_md.exists():
        print(f"ERROR: input markdown not found: {input_md}")
        return 1

    try:
        export_markdown_to_pdf(
            input_md=input_md,
            output_pdf=output_pdf,
            page_budget=args.page_budget,
            pdf_engine=args.pdf_engine,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Exported PDF resume: {output_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
