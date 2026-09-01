# Backend

FastAPI service for tenant-isolated ingestion, sparse retrieval, cited generation, deterministic
evaluation, audit events, and operational telemetry. PostgreSQL is required in production; SQLite
is available only for development and tests.

## Development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Development uses the local principal configured in `.env.example`. Production rejects disabled
authentication and unsafe data-service configuration.

## Quality gates

```bash
ruff check app tests scripts
ruff format --check app tests scripts
mypy app
pytest --cov=app --cov-report=term-missing
python -m scripts.run_retrieval_eval
DATABASE_URL=sqlite:////tmp/migration.db ENVIRONMENT=test alembic upgrade head
pip-audit -r requirements-dev.txt
```

See the repository [README](../README.md), [API authentication](../docs/api-authentication.md), and
[Deployment guide](../docs/deployment.md).
