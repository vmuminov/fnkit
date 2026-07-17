.PHONY: stylecheck_fix stylecheck typecheck test verify verify_ci
.SILENT: stylecheck_fix stylecheck typecheck test verify verify_ci

.DEFAULT_GOAL := verify

PY      := uv run
RUFF    := $(PY) ruff
PYTEST  := $(PY) pytest
PYRIGHT := $(PY) pyright

stylecheck_fix:
	$(RUFF) check --fix .
	$(RUFF) format .

stylecheck:
	$(RUFF) check .
	$(RUFF) format --check .

typecheck:
	$(PYRIGHT)

test:
	$(PYTEST)

verify: stylecheck_fix typecheck test
verify_ci: stylecheck typecheck test
