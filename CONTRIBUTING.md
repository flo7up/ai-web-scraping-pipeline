# Contributing

Thanks for considering a contribution.

## Local Setup

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt
./.venv/Scripts/python.exe -m pytest
```

## Pull Request Expectations

- Keep changes focused.
- Add or update tests when behavior changes.
- Do not commit secrets or environment-specific settings.
- Prefer configuration over hardcoded domain logic.
- Keep prompt changes small and explain why they are needed.

## Development Notes

This project is intended to stay generic. Domain-specific behavior should live in `pipeline.config.json`, prompt templates, or example files unless it is broadly useful.
