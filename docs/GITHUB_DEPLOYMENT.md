# GitHub Upload and Deployment Checklist

## Upload correctly

The repository root must contain `streamlit_app.py`; do not upload one extra outer folder.

```bash
git init
git add .
git commit -m "Build AI resume intelligence platform"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

## Never upload

- `.env`
- `.streamlit/secrets.toml`
- `.venv`
- `resume_analyzer.db`
- real resumes or recruiter data
- database passwords or API keys

The included `.gitignore` blocks these files.

## Before deployment

```bash
python scripts/preflight.py
pytest -q
```

## GitHub portfolio polish

- Add the deployed Streamlit URL in the repository About section.
- Pin the repository on your GitHub profile.
- Add 2–3 screenshots after deployment.
- Keep README architecture and demo instructions visible.
- Use meaningful commit messages instead of one giant `final code` commit.
