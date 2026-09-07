## What does this pull request change?

<!-- One or two sentences. What problem does this solve? -->

Closes #<!-- issue number -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor (no behaviour change)
- [ ] Documentation
- [ ] CI/CD or tooling

## How was it tested?

<!-- Name the tests you added or changed, and how you checked the behaviour
     manually. "It works" is not evidence. -->

- [ ] I added or updated automated tests
- [ ] The full suite passes locally (`pytest`)
- [ ] I ran the application and exercised the change by hand

## Checklist

- [ ] `ruff check .` passes
- [ ] `black --check .` passes
- [ ] `bandit -c pyproject.toml -r app -ll` passes
- [ ] Coverage is at or above the 85% gate
- [ ] No secrets, credentials or `.env` files are committed
- [ ] Documentation is updated if the behaviour changed

## Evidence

<!-- Screenshot of the passing CI run, and of the feature working. -->

## Notes for the reviewer

<!-- Anything you want the reviewer to look at closely, or a decision you are
     unsure about. -->
