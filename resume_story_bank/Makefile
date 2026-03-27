.PHONY: validate-story-bank validate validate-resume-model generate-resume export-pdf test-resume-pipeline temp-dir clean-temp

MODEL ?= tests/fixtures/sample_resume_model.json
OUTPUT ?= resumes/tailored/generated
PAGE_BUDGET ?= 2
PDF_ENGINE ?=
TEMP_DIR ?= /tmp/resume_story_bank_temp

validate-story-bank:
	python3 scripts/validate_story_bank.py

validate: validate-story-bank

validate-resume-model:
	python3 scripts/validate_resume_model.py --input $(MODEL)

generate-resume:
	python3 scripts/generate_resume_artifacts.py --input-model $(MODEL) --output-dir $(OUTPUT) --page-budget $(PAGE_BUDGET) $(if $(PDF_ENGINE),--pdf-engine $(PDF_ENGINE),)

export-pdf:
	python3 scripts/export_pdf.py --input $(OUTPUT)/resume.md --output $(OUTPUT)/resume.pdf --page-budget $(PAGE_BUDGET) $(if $(PDF_ENGINE),--pdf-engine $(PDF_ENGINE),)

test-resume-pipeline:
	python3 -m unittest discover -s tests -p "test_*.py"

temp-dir:
	mkdir -p $(TEMP_DIR)

clean-temp:
	mkdir -p $(TEMP_DIR)
	rm -rf $(TEMP_DIR)/*
