# CHUNGUS Language
A clean, minimal, general programming language.

## Tech Stack
- Python

## Get Started
1. Install `Python`, version `3.12.3` was used to develop initialize project.
2. Create a virtual environment. For CMD or PowerShell, run `python -m venv .venv`. For Bash, run `python3 -m venv .venv`.
3. Activate the virtual environment. For CMD, run `.venv\Scripts\activate`. For PowerShell, run `.venv\Scripts\Activate.ps1`. For Bash, run `source .venv/bin/activate`.
4. Run the main file `python -m src.main`
  - Run the lexer module `python -m src.lexer` (It would use the test file: `lexer_test.chg`)

## How to contribute in project?
- Make sure to create git branch before any changes. Do `git branch` to check which branch you are in. `git checkout -b <name>`. You can now apply changes in the code.
- Merge your changes with the main try `git fetch` then `git merge origin/main`, then push to a remote branch.
