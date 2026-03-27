.PHONY: validate-story-bank validate-story-metadata validate validate-resume-model validate-resume-model-strict tailor-resume-model generate-resume export-pdf test-resume-pipeline temp-dir clean-temp

MODEL ?= tests/fixtures/sample_resume_model.json
OUTPUT ?= resumes/tailored/generated
PAGE_BUDGET ?= 2
PDF_ENGINE ?=
TEMP_DIR ?= /tmp/resume_story_bank_temp
BASE_RESUME ?= tests/fixtures/sample_base_resume.md
JOB_DESCRIPTION ?= tests/fixtures/sample_job_description.md
STORY_BANK ?= tests/fixtures/sample_story_bank.md
EMBEDDING_CACHE ?= $(HOME)/.cache/resume_story_bank/embedding_cache.json

validate-story-bank:
	python3 scripts/validate_story_bank.py

validate-story-metadata:
	python3 scripts/validate_story_bank_metadata.py

validate: validate-story-bank validate-story-metadata

validate-resume-model:
	python3 scripts/validate_resume_model.py --input $(MODEL)

validate-resume-model-strict:
	python3 scripts/validate_resume_model.py --input $(MODEL) --master-story-bank data/processed/master_story_bank.md

tailor-resume-model:
	python3 scripts/tailor_resume_model.py --base-resume $(BASE_RESUME) --job-description $(JOB_DESCRIPTION) --master-story-bank $(STORY_BANK) --embedding-cache $(EMBEDDING_CACHE) --output $(MODEL) --page-budget $(PAGE_BUDGET)

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
