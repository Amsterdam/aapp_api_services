# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project overview

- Python / Django REST Framework backend for the Amsterdam App. It provides information, communication, and transaction services for residents, entrepreneurs, and visitors of Amsterdam.
- Python version: >=3.14,<3.15. Django and Django REST Framework dependencies are declared in `pyproject.toml` and exported to `requirements.txt`.
- Database: PostgreSQL. Background jobs: Redis.

## Setup and commands

Always use these commands. Do not invent alternatives.

```bash
# Install dependencies inside the active virtual environment
uv pip install -r requirements.txt

# Run tests and lint checks across all services (Docker Compose)
make test

# Run tests for one service
SERVICE_NAME=city_pass make test

# Run a selected test file for one service
SERVICE_NAME=city_pass docker compose run --rm test pytest city_pass/tests/test_authentication.py

# Lint and format
make lintfix

# Verify there are no missing migrations
SERVICE_NAME=city_pass make migrations --check --dry-run
```

## Project structure

```
manage.py           Django management entry point
core/               Shared settings, authentication, middleware, and utilities
bridge/             Group of bridge services, with nested service modules
city_pass/          Service-specific Django app
construction_work/  Service-specific Django app
news/               Service-specific Django app
contact/             Service-specific Django app
image/               Service-specific Django app
modules/             Service-specific Django app
notification/        Service-specific Django app
waste/               Service-specific Django app
survey/              Service-specific Django app
```

Service apps generally contain their own `settings/` and `tests/` directories; shared functionality belongs in `core/`.

## Code conventions

- Follow the existing style in the surrounding code before introducing new patterns.
- Type hints on all new functions and methods.
- Keep views thin. Put business logic in `services.py` and queries in `selectors.py`.
- Avoid N+1 queries: use `select_related` / `prefetch_related` where related objects are accessed.
- Wrap multi-step writes in `transaction.atomic()`.
- Use the ORM. No raw SQL unless there is no reasonable alternative, and explain why in the PR.
- Never hardcode secrets or environment-specific values. Read them from settings / environment variables.
- Prefer explicit over clever. No new abstractions for a single use.

## Testing

- Every behavior change needs tests. Bug fixes need a test that fails before the fix.
- Write tests first when the acceptance criteria are clear, then implement until they pass.
- Use pytest tests and `model_bakery` to construct model instances. No reliance on fixtures with hidden state.
- Test behavior (inputs and outputs, API responses, DB state), not implementation details.
- Do not mock the database. Mock only external services.
- Tests must be deterministic: no real network calls, no dependence on current time without freezing it.

## Migrations

- Generate migrations with `makemigrations`.
- Never edit or delete an existing migration that may already be applied elsewhere.
- Separate schema changes from data migrations.
- Flag any migration that locks large tables, drops columns, or is not backwards compatible in the PR description.

## Boundaries

Do NOT, without explicit approval in the ticket or PR discussion:

- Add, remove or upgrade dependencies.
- Change settings, CI configuration, Docker or deployment files.
- Modify authentication, permissions or payment-related logic beyond what the ticket requires.
- Make changes unrelated to the ticket (no drive-by refactors; mention them in the PR instead).
- Touch generated files or vendored code.

## Workflow for a ticket

1. Read the ticket (Jira key format: `AM-123`). If acceptance criteria are missing or ambiguous, list your open questions first instead of guessing.
2. Write a short plan: affected files, migrations, edge cases, test strategy.
3. Implement in small steps, running tests and linters as you go.
4. Before finishing, run: `make lintfix`, `SERVICE_NAME=city_pass make test`, `ruff format --check .`, `mypy .`, `pytest`, `makemigrations --check`. All must pass.
5. Review your own diff against the acceptance criteria and remove anything out of scope.

## Git and pull requests

- Branch name: `service-name/AM-123-short-description` or `fix/AM-123-short-description`.
- Commits: small and focused. Format: `AM-123: imperative summary`.
- PR title: `AM-123: short summary`.
- PR description must contain:
  - Link or key of the Jira ticket
  - What changed and why
  - How it was tested
  - Risks, migrations, or follow-ups
- Keep PRs small. If a ticket is too large, propose a split instead of delivering one big PR.

## Definition of done

- Acceptance criteria met and covered by tests
- Tests, lint and type checks pass
- No unintended migrations or leftover debug code
- PR description is complete
