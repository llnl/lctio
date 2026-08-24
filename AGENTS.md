# Repository Guidelines

LCTIO is a Python package with source in `src/lctio/`, tests in `tests/`, and project settings in `pyproject.toml`.

Before editing, rebasing work, or relying on earlier observations, refresh the current repository state. Use commands such as `git status`, `git log --oneline -n 10`, `ls -lt src tests`, or file mtime checks. Do not assume the filesystem is unchanged between agent tasks or after an interrupted session.

Detailed repository guidance is split into repo-local skills under `.agents/skills/`.
