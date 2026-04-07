# Repository Guidelines

## Project Structure & Module Organization
This repository uses a service-oriented Python monorepo layout under `src/`.

When adding code, keep the layout explicit:
- `src/admin_bot/` for Telegram admin bot logic
- `src/userbot_worker/` for Telethon user session workers
- `src/chatbot_service/` for chatbot orchestration and business flow
- `src/shared/` for cross-service packages (`domain`, `config`, `queue`, `persistence`, `logging`)
- `tests/` for automated tests
- `scripts/` for one-off developer utilities
- `docs/` for design notes or operational documentation

Avoid placing importable Python code at the repository root.

## Build, Test, and Development Commands
Canonical local commands:
- `python -m pip install -e '.[dev]'` to install project and developer tooling
- `python -m ruff check .` for linting
- `python -m ruff format . --check` for format checks
- `python -m pytest` to run tests
- `python -m shared.persistence.migrator up` to apply schema migrations

If you change tooling or commands, update this file and `README.md` in the same change.

## Coding Style & Naming Conventions
The ignore rules indicate a Python workflow, so use standard Python conventions unless the repository adopts a formatter later:
- 4-space indentation
- `snake_case` for modules, functions, and variables
- `PascalCase` for classes
- small, single-purpose modules under the `src/` service packages

Prefer type hints for new public functions and keep side-effect-heavy scripts inside `scripts/`.

## Testing Guidelines
Use `python -m pytest` for test execution. New features should include tests under `tests/`, with files named `test_<feature>.py`.

## Commit & Pull Request Guidelines
The current history contains a single commit: `Initial commit`. No formal convention is established, so use short imperative commit subjects such as `Add lease parser module`.

Pull requests should include:
- a brief summary of the change
- any new commands or setup steps
- linked issue or task reference, if one exists
- sample input/output when behavior changes are user-visible

## Repository Maintenance
Keep `AGENTS.md` repository-specific. If you add core tooling, directories, or architectural constraints, update this guide immediately so future contributors inherit the current workflow instead of guessing.

## Task Context Documents
For large-repository agent runs, prefer the compact context files under `docs/task_context/` before scanning broad directories:
- `architecture_schema.md`
- `domain_schema.md`
- `database_schema.md`
- `repository_contract.md`
- `file_map.md`
- `testing_contract.md`
- `workflow_contract.md`

If a change updates one of those source-of-truth areas, update the matching context file in the same change.
