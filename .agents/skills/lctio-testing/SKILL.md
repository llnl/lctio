---
name: lctio-testing
description: Use when writing or updating pytest coverage for TIFF handling, CLI behavior, or other tests in this repository.
---

# LCTIO Testing

Use this skill for test additions, fixture design, and coverage-oriented validation.

## Pytest Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Prefer `tmp_path` for filesystem tests.

## Commands

- `python -m pytest`
- `pytest --cov=lctio --cov-report=term`
- `pytest --cov=lctio --cov-report=term --cov-report=xml:reports/junit/coverage.xml --junit-xml=reports/junit/pytest.xml`

## Expectations

- New behavior should ship with direct tests.
- Use coverage output to identify untested code paths when a change is non-trivial.
- Keep tests deterministic; prefer seeded random data for generated image fixtures.

## TIFF-Specific Guidance

For compressed TIFF fixtures and dtype edge cases, read [references/tiff-fixtures.md](references/tiff-fixtures.md).
