## Linting (flake8)

This project recommends using flake8 to check style and simple errors.

Run flake8 over the codebase:
```sh
# from repository root
flake8 .
flake8 src test
```

Flake8 Project config:
- Project-level flake8 config is in [`.flake8'](.flake8). Keep this file in version control so all contributors share the same rules.
  - Common options:
    - `--max-line-length` to set a project line length.
    - `--ignore`/`--select` to tune which errors to check.

Editor integration:
- VS Code: install the "Python" extension and set the linter to flake8 (Preferences → "Python: Linting Flake8 Enabled").
- Optionally add a pre-commit hook to run flake8 before commits.
