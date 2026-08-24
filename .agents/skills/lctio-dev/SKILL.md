---
name: lctio-dev
description: Use when working on LCTIO development setup, editable installs, linting, formatting, type checking, or packaging.
---

# LCTIO Dev

Use this skill for local environment setup and standard validation commands.

## Workflow

1. Check whether `.venv/` already exists before creating a new virtual environment.
2. Use Python 3.10+.
3. Install the project in editable mode with `python -m pip install -e .`.

## Core Commands

- `python -m pytest`
- `python -m black src tests`
- `python -m ruff check src tests`
- `python -m mypy src`
- `python -m build`
- `retiff --help`

## Notes

- Build output may appear in `dist/` and `src/lctio.egg-info/`; treat both as generated artifacts.
- Repository settings for Black, Ruff, mypy, pytest, and packaging live in `pyproject.toml`.
- Prefer validating only the commands relevant to the files you changed, then run broader checks when the change is cross-cutting.
