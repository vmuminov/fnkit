.PHONY: lint check pylance test verify verify_ci
.SILENT: lint check  pylance test verify verify_ci

.DEFAULT_GOAL := verify

PY      := uv run
RUFF    := $(PY) ruff
PYTEST  := $(PY) pytest
PYRIGHT := $(PY) pyright

lint:
	$(RUFF) check --fix .
	$(RUFF) format .

check:
	$(RUFF) check .
	$(RUFF) format --check .

pylance:
	$(PYRIGHT)

test:
	$(PYTEST)

verify: lint pylance test
verify_ci: check pylance test
