# Contributing

Short version. The full workflow is in [`docs/git-workflow.md`](docs/git-workflow.md).

## Before you start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

## The cycle

```
issue → branch from develop → commits → push → PR → CI → review → merge
```

1. **Open an issue** using a template in `.github/ISSUE_TEMPLATE/`. Write
   objectively checkable acceptance criteria before writing code.
2. **Branch from `develop`:** `feature/…`, `fix/…`, `docs/…`, `chore/…`, `test/…`
3. **Commit in Conventional Commits format:** `feat(auth): lock accounts after
   five failed sign-ins`. Explain *why* in the body.
4. **Run the gates locally before pushing:**
   ```bash
   ruff check . && black --check . && bandit -c pyproject.toml -r app -ll && pytest
   ```
5. **Open a pull request**, fill in the template, link the issue with `Closes #N`.
6. **Wait for CI.** A red pipeline is not ready for review.
7. **Get a review.** One approval is required; CODEOWNERS requests the right
   person automatically.
8. **Address feedback** with follow-up commits — do not force-push during review.
9. **Squash and merge**, then delete the branch.

## Code standards

- Black formatting, 100 columns
- Ruff clean (`E,F,W,I,B,C4,UP,SIM,ARG,RET,N`)
- Type hints on public functions
- Docstrings explain *why*, not *what*
- Tests for new behaviour, including the negative cases
- Coverage at or above 85%

## Architectural rules

- Routes must not contain queries or business rules
- Repositories must not contain business rules
- Every state change writes an audit entry, in the **same transaction**
- Authorisation is checked in the service, not only in the route
- Validation is applied in the service, not only in the form
- Never build SQL by string concatenation

## Never commit

`.env`, secrets, tokens, `*.db`, `.venv/`, `__pycache__/`, coverage output.

If you commit a secret by accident, **rotate it immediately** — removing it from
history does not un-leak it.
