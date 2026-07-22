.PHONY: install run debug clean lint lint-strict

install:
	pip install -r requirements.txt
	pip install mazegenerator-00001-py3-none-any.whl

run:
	python pac-man.py config.json

debug:
	python -m pdb pac-man.py config.json

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .mypy_cache

lint:
	flake8 src/ pac-man.py

lint-strict:
	flake8 src/ pac-man.py && mypy src/ pac-man.py \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs
