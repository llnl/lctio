---
name: lctio-docs
description: Use when updating Sphinx documentation, changing docs/source/conf.py, adding Sphinx extensions, or validating documentation builds for this repository.
---

# LCTIO Docs

Use this skill for changes under `docs/`, Sphinx configuration updates, and documentation build validation.

## Workflow

1. Refresh repository state before editing.
2. If `./.venv/` exists, use `./.venv/bin/python` and tools from that environment for docs installs and builds.
3. Inspect `docs/source/conf.py`, `docs/Makefile`, and any new docs files you will touch.
4. Check `pyproject.toml` for the current packaging and dependency layout before assuming docs dependencies exist.
5. For `autodoc` and related extensions, prefer installing the project in editable mode with the local virtual environment so imports resolve from `src/`.
6. Manage docs-only dependencies with a docs extra in `pyproject.toml`.
7. Run a clean docs build after config or content changes and treat warnings as important review items.

## Core Commands

- `./.venv/bin/python -m pip install -e .`
- `./.venv/bin/python -m pip install -e .[docs]`
- `PATH="$PWD/.venv/bin:$PATH" make -C docs html`
- `./.venv/bin/python -m sphinx -b html docs/source docs/build/html`
- `./.venv/bin/python -m sphinx -W -b html docs/source docs/build/html`
- `make -C docs clean`
- `PATH="$PWD/.venv/bin:$PATH" make -C docs clean`
- `./.venv/bin/python -m sphinx -b linkcheck docs/source docs/build/linkcheck`
- `./.venv/bin/python -m sphinx -b doctest docs/source docs/build/doctest`

## Autodoc Notes

- If Sphinx cannot import `lctio`, first verify the editable install rather than immediately patching `sys.path`.
- If runtime-only dependencies break docs imports, prefer `autodoc_mock_imports` for optional packages instead of hiding real import failures from this package.

## What To Confirm With The User

- Which Sphinx extensions and themes are approved for the project.
- Whether warnings should fail validation by default with `-W` for the current change.
- Whether a failure is likely caused by local environment constraints, optional dependencies, or network access.

## Expectations

- Keep generated docs output under `docs/build/` treated as generated unless the user asks to commit it.
- Prefer validating only the docs targets affected by the change, then run a stricter warning-failing build when the change touches configuration or shared content.
- Investigate warnings and validation failures enough to identify whether they are actionable code or docs issues versus environment-sensitive failures.
- For `linkcheck`, external links may fail because of transient network or remote-site behavior; report that clearly instead of treating every failure as a docs defect.
- For doctest or example-code validation, expect some failures to depend on local environment state. Do not spend extended effort on repeated or ambiguous failures before consulting the user.
