PY ?= .venv/bin/python

.PHONY: install test test-all test-browser coverage demos animations lab notebooks-check clean readme-media site api dist

install:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	$(PY) -m ipykernel install --user --name quantum-playground

# Fast loop: skips tests marked slow (site build, big simulations).
test:
	$(PY) -m pytest

# Everything, as CI runs it.
test-all:
	$(PY) -m pytest -m ""

# Only the explorer's browser tests (needs: pip install -e ".[browser]" && python -m playwright install chromium).
test-browser:
	QPLAY_REQUIRE_BROWSER=1 $(PY) -m pytest -m "" tests/test_explorer.py

# Everything, with a line-by-line coverage report (fails under the threshold in pyproject.toml).
coverage:
	$(PY) -m pytest -m "" --cov=qplay --cov-report=term-missing

demos:
	$(PY) -m qplay run all --out figures

lab:
	$(PY) -m jupyter lab

# Execute every notebook top to bottom; fails if any cell raises.
notebooks-check:
	for f in notebooks/*.ipynb lessons/*.ipynb; do \
	  env -u MPLBACKEND $(PY) -m jupyter nbconvert --to notebook --execute --stdout "$$f" > /dev/null || exit 1; \
	done

clean:
	rm -rf figures .pytest_cache .coverage build dist src/*.egg-info _site

animations:
	$(PY) -m qplay animate all --out figures

readme-media:
	$(PY) scripts/make_readme_media.py docs/images

site:
	$(PY) scripts/build_site.py _site

# API reference only, from the docstrings, into _site/api.
api:
	$(PY) -m pdoc qplay --math -o _site/api

# Wheel and sdist into dist/ (the release workflow publishes these on a version tag).
dist:
	rm -rf dist
	$(PY) -m build
