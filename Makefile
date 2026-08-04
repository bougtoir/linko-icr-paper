PYTHON ?= .venv/bin/python
ITER ?= 1000
CONV_ITER ?= 500
SENS_ITER ?= 500

.PHONY: all setup data analysis manuscript audit lint clean

all: analysis audit manuscript

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

data:
	bash scripts/download_ist.sh

analysis: data
	$(PYTHON) run_analysis.py --iterations $(ITER) \
		--convergence-iterations $(CONV_ITER) \
		--sensitivity-iterations $(SENS_ITER)

audit:
	$(PYTHON) scripts/audit_manuscript.py

manuscript:
	$(PYTHON) generate_docx.py
	$(PYTHON) generate_pptx.py
	$(PYTHON) scripts/generate_cover_letter.py

lint:
	$(PYTHON) -m ruff check --select F,E9 src scripts generate_docx.py generate_pptx.py run_analysis.py

clean:
	rm -rf results figures/submission
