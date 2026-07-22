# All targets are actions, not files, so list them as phony (always run them).
.PHONY: install run debug clean fclean lint lint-strict

# The venv's python. Every rule uses "$(PY) -m <tool>" so it always runs the
# python AND the tools (pip, flake8, mypy) that live INSIDE the venv.
# NOTE: this path is for Linux/Mac (where 42 reviews run). On Windows the venv
# uses venv/Scripts/python instead — test on Linux or WSL.
PY = venv/bin/python

# Create the venv (if missing), then install every dependency INTO it.
install:
      python3 -m venv venv
      $(PY) -m pip install --upgrade pip
      $(PY) -m pip install -r requirements.txt

# Launch the game, using the venv's python.
run:
      $(PY) pac-man.py config.json

# Launch inside Python's built-in debugger (pdb) for step-by-step debugging.
debug:
      $(PY) -m pdb pac-man.py config.json

# Mandatory lint: style (flake8) AND types (mypy) with the exact required flags.
lint:
      $(PY) -m flake8 .
      $(PY) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# Optional stricter type check: flake8 plus mypy in full --strict mode.
lint-strict:
      $(PY) -m flake8 .
      $(PY) -m mypy . --strict

# Remove Python caches/artifacts, but KEEP the venv (rebuilding it is slow).
clean:
      find . -type d -name __pycache__ -exec rm -rf {} +
      rm -rf .mypy_cache
      find . -name "*.pyc" -delete

# Full clean: everything clean does, PLUS delete the venv for a fresh start.
fclean: clean
      rm -rf venv