# Simple Makefile for Nova Sonic Speech Agent
.PHONY: install test format build clean

install:
	pip install -e ".[dev]"

test:
	pytest

format:
	black src/ tests/
	ruff check --fix src/ tests/

build:
	python -m build

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -name __pycache__ -exec rm -rf {} +

install-cli: build
	pip install dist/*.whl --force-reinstall