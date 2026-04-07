# Task Context Pack

This directory exists to reduce broad repository scanning during agent-driven work, especially as the repository grows.

These files are the preferred high-signal context entry points for this repository:

- `architecture_schema.md`: package boundaries, dependency rules, and extension points
- `domain_schema.md`: shared business entities, enums, and invariants
- `database_schema.md`: current PostgreSQL schema summary and storage rules
- `repository_contract.md`: repository-wide source-of-truth rules and public contracts
- `file_map.md`: where code, docs, tests, and operational files live
- `testing_contract.md`: test layout, commands, fixtures, and execution expectations
- `workflow_contract.md`: branch, push, review, and PR delivery expectations

Preferred execution model:

1. Read the task or user request.
2. Read only the task-context files needed for that scope.
3. Avoid scanning unrelated source packages or unrelated tests unless blocked by a missing fact.
4. If blocked, report the missing fact before reading more files.
