PY ?= .venv/bin/python

.PHONY: install test demos animations lab notebooks-check clean

install:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	$(PY) -m ipykernel install --user --name quantum-playground

test:
	$(PY) -m pytest

demos:
	$(PY) -m qplay run all --out figures

lab:
	$(PY) -m jupyter lab

# Execute every notebook top to bottom; fails if any cell raises.
notebooks-check:
	for f in notebooks/*.ipynb; do \
	  env -u MPLBACKEND $(PY) -m jupyter nbconvert --to notebook --execute --stdout "$$f" > /dev/null || exit 1; \
	done

clean:
	rm -rf figures .pytest_cache build dist src/*.egg-info

animations:
	$(PY) -m qplay animate all --out figures
