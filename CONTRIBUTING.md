# Contributing to AutoBarcoder

Thanks for thinking about contributing! Bug reports, feature ideas, doc improvements, and PRs are all welcome.

## Getting set up

```bash
git clone https://github.com/abachu2005/AutoBarcoder-OS-.git
cd AutoBarcoder-OS-
python3 bin/autobarcoder-setup        # creates .venv, installs deps, smoke-tests
```

This installs the runtime dependencies plus the web-UI extras. For development:

```bash
./.venv/bin/pip install -e ".[dev]"   # editable + pytest + ruff + pre-commit
./.venv/bin/pre-commit install        # auto-format + lint on every commit
```

## Running tests

```bash
./.venv/bin/pytest -q
```

CI runs the same tests on Python 3.9, 3.10, 3.11, and 3.12.

## Code style

- Formatting/linting via [ruff](https://docs.astral.sh/ruff/) (configured in `pyproject.toml`).
- Run `ruff check . && ruff format .` (pre-commit does this automatically).
- Type hints encouraged on new code; no strict mypy gate for now.

## Sending a pull request

1. Fork the repo and create a branch from `main`.
2. Make your change. Add or update tests under `tests/` and the `CHANGELOG.md` "Unreleased" section.
3. Make sure `pytest` and `ruff check .` pass locally.
4. Open a PR against `main`. Fill in the PR template.

## Reporting bugs / requesting features

Use the GitHub issue tracker — there are bug-report and feature-request templates in `.github/ISSUE_TEMPLATE/`.

## Code of Conduct

Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).
