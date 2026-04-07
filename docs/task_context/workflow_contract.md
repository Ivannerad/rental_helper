# Workflow Contract

This file defines repository-wide delivery expectations for autonomous task execution.

## Branch and publication rules

- Create a dedicated local branch when a task changes tracked files.
- Push to `origin` only when the task or user explicitly requires remote publication.
- Open a pull request only when the task or user explicitly requires PR delivery.
- Do not assume branch push, PR creation, labeling, or reviewer assignment unless it is requested.

## Explicit workflow requirements

When a task depends on GitHub delivery, it should state the workflow in direct terms instead of leaving it implicit. Good examples:

- `Create a local branch for this change.`
- `Push the final branch to origin.`
- `Open a pull request against main.`
- `Include validation results in the PR body.`

## Review and completion

- If a task uses separate implementation and review phases, final delivery should wait for both.
- Address blocking review findings before remote publication.
- If review notes are non-blocking, summarize them in the final report or PR body.

## Context budget rule

- Large-repository tasks should explicitly list the allowed context files.
- Do not assume full-repository scans are acceptable when the task provides a narrower context pack.
