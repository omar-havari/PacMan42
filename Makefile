.PHONY: install run debug clean lint lint-strict

install:
	pip install -r requirements.txt

run:
	python src/main_menu_UI.py

debug:
	python -m pdb src/main_menu_UI.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .mypy_cache

lint:
	flake8 src/

lint-strict:
	flake8 src/ && mypy src/ \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs
