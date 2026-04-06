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
No canonical build, run, lint, or test commands are defined yet. Do not invent project commands in commits or pull requests. If you introduce tooling, update this file in the same change.

Expected examples once tooling exists:
- `python -m pytest` to run tests
- `python -m ruff check .` for linting
- `python -m ruff format .` for formatting

Document any new local setup in [`README.md`](/home/ivan/work yourself/rental_helper/README.md).

## Coding Style & Naming Conventions
The ignore rules indicate a Python workflow, so use standard Python conventions unless the repository adopts a formatter later:
- 4-space indentation
- `snake_case` for modules, functions, and variables
- `PascalCase` for classes
- small, single-purpose modules under the `src/` service packages

Prefer type hints for new public functions and keep side-effect-heavy scripts inside `scripts/`.

## Testing Guidelines
There is no test framework configured yet. New features should include tests under `tests/`, with files named `test_<feature>.py`. If you add a test runner or coverage tool, record the exact command here and in the README.

## Commit & Pull Request Guidelines
The current history contains a single commit: `Initial commit`. No formal convention is established, so use short imperative commit subjects such as `Add lease parser module`.

Pull requests should include:
- a brief summary of the change
- any new commands or setup steps
- linked issue or task reference, if one exists
- sample input/output when behavior changes are user-visible

## Repository Maintenance
Keep `AGENTS.md` repository-specific. If you add core tooling, directories, or architectural constraints, update this guide immediately so future contributors inherit the current workflow instead of guessing.
