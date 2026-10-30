# Production Deployment Guide — Echo Journal (Milestone 6)

This guide documents deploying Echo Journal to production environments with strict security, rate limiting, and zero-friction database swapping to PostgreSQL.

---

## 1. Production Architecture Checklist

- [x] **Database**: PostgreSQL with connection pooling (`DATABASE_URL=postgresql://...`).
- [x] **Rate Limiting**: Sliding window rate limiter active on `/auth/login` and `/auth/register`.
- [x] **Security Headers**:
  - `Content-Security-Policy`: Disallows untrusted external scripts.
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- [x] **Session Flags**: `HttpOnly`, `SameSite=Lax`, and `Secure=true` in production.
- [x] **Data Isolation**: Verified via `tests/test_isolation.py` and `tests/test_admin.py`.

---

## 2. Docker Deployment

### `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-ml.txt gunicorn

# Copy application files
COPY . .

# Run as non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

ENV FLASK_ENV=production
ENV SESSION_COOKIE_SECURE=true

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "wsgi:app"]
```

---

## 3. Free-Tier Cloud Deployments

### Option A: Render (Web Service + Managed PostgreSQL)
1. Fork or push your Echo Journal repository to GitHub.
2. In the Render Dashboard, create a **New PostgreSQL** database (free tier). Copy the Internal Database URL.
3. Create a **New Web Service**:
   - Build Command: `pip install -r requirements.txt -r requirements-ml.txt`
   - Start Command: `gunicorn wsgi:app`
4. Add Environment Variables:
   - `DATABASE_URL`: Your PostgreSQL connection string.
   - `SECRET_KEY`: A 64-character high-entropy secret string (`python -c "import secrets; print(secrets.token_hex(32))"`).
   - `SESSION_COOKIE_SECURE`: `true`.
5. Run the schema initialization or migration tool:
   ```bash
   python scripts/migrate_to_postgres.py --pg-url $DATABASE_URL
   ```

### Option B: Railway or Fly.io
1. Connect GitHub repository.
2. Provision a free PostgreSQL database.
3. Attach environment variables (`DATABASE_URL`, `SECRET_KEY`).
4. Railway/Fly automatically detects the `Procfile` or `Dockerfile`.

---

## 4. Database Engine Swap (SQLite ➔ PostgreSQL)

Echo Journal uses a repository layer that separates SQL dialect from domain logic:

1. **Development**: Runs out of the box with zero configuration using SQLite (`echo_journal.db` with WAL mode).
2. **Production Swap**:
   - Provide `DATABASE_URL=postgresql://user:password@host:port/database`.
   - Run the automated migration script:
     ```bash
     python scripts/migrate_to_postgres.py --sqlite-path echo_journal.db --pg-url $DATABASE_URL
     ```
   - Zero code modification is needed in `app/`.
