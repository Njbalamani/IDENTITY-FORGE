# Deployment Guide

## Local development

Use SQLite for fast local startup. Copy `.env.example` to `.env`, install dependencies, migrate, seed and run the development server.

```powershell
scripts\setup.ps1
scripts\dev.ps1
```

## Production stack

```powershell
Copy-Item .env.example .env
docker compose -f docker\docker-compose.yml --env-file .env up --build -d
```

The compose stack waits for PostgreSQL and Redis readiness, runs an HTTP liveness check against the web service before starting Nginx, and restarts services automatically.

Before production-style use:

- Generate a strong `DJANGO_SECRET_KEY`.
- Set `DEBUG=False`.
- Set `ALLOWED_HOSTS` to real hostnames.
- Set `DATABASE_ENGINE=django.db.backends.postgresql`.
- Set strong PostgreSQL credentials.
- Set `REDIS_URL` to the production broker.
- Enable HTTPS settings and secure cookies.
- Keep `SYNTHETIC_DATA_ONLY=True` for demonstrations.

## Operations

```powershell
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py identityforge_health --json
python manage.py seed_identityforge
python manage.py generate_sample_data
```

Celery worker:

```powershell
celery -A config worker --loglevel=info
```

## Backup considerations

Back up PostgreSQL volumes, the generated reports directory and the media volume. Audit logs are database records and should be retained according to your own policy.
