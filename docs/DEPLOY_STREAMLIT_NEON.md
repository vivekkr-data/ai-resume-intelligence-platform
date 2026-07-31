# Free Deployment: Streamlit Community Cloud + Neon PostgreSQL

This is the recommended recruiter-demo deployment because Streamlit hosts the UI while Neon provides persistent PostgreSQL storage.

## 1. Push the project to GitHub

The repository root must directly contain:

```text
streamlit_app.py
requirements.txt
backend/
data/
migrations/
```

Do not upload `.env`, `.streamlit/secrets.toml`, database files or `.venv`.

## 2. Create the PostgreSQL database

1. Create a Neon account and project.
2. Open the project dashboard and choose **Connect**.
3. Copy the PostgreSQL connection string.
4. Keep `sslmode=require` in the URL.

Typical format:

```text
postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

The application normalizes this URL for psycopg 3 automatically.

## 3. Deploy the Streamlit app

1. Sign in to Streamlit Community Cloud using GitHub.
2. Create a new app from this repository.
3. Branch: `main`
4. Main file: `streamlit_app.py`
5. Python: 3.11

## 4. Add secrets

In Streamlit App settings → Secrets, paste:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"
APP_ENV = "production"
STORE_PII = "false"
ADMIN_DASHBOARD_PIN = "a-private-pin"
ADMIN_API_KEY = "a-long-random-string"
```

Never commit real credentials to GitHub.

Official references:

- Streamlit secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Streamlit PostgreSQL tutorial: https://docs.streamlit.io/develop/tutorials/databases/postgresql
- Neon Python connection guide: https://neon.com/docs/guides/python

## 5. Verify deployment

1. Open the app.
2. The sidebar should show `Database: PostgreSQL` and `Database health: Connected`.
3. Upload the sample resume.
4. Load the recruiter demo JD.
5. Run analysis.
6. Refresh the browser and confirm PostgreSQL still contains the analysis through the admin dashboard.

## 6. Common errors

### Password contains special characters

Use the exact connection string copied from Neon. Do not manually edit or expose the password.

### Connection timeout

Confirm the URL includes `sslmode=require`, the database is active, and the whole URL is stored as one quoted secret.

### Sentence Transformer download is slow

The model downloads on first use. Open the deployed app and run one analysis before your interview so the cache is warm.

### App shows SQLite

`DATABASE_URL` was not loaded. Recheck the exact secret name and redeploy/reboot the app.

## Render alternative

`render.yaml` is included. Add the same `DATABASE_URL`, `ADMIN_DASHBOARD_PIN` and `ADMIN_API_KEY` as environment variables. Render free PostgreSQL is not ideal for long-term demo persistence because its current free database has an expiration period; an external hosted PostgreSQL service is safer for an interview link.
