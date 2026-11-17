ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif
.PHONY: test test-live smoke smoke-live
test:
	$(PYTHON) -m pytest -q -m "not live"
test-live:
	$(PYTHON) -m pytest -q -m live
smoke:
	$(PYTHON) scripts/smoke.py
smoke-live:
	$(PYTHON) scripts/smoke.py --live
