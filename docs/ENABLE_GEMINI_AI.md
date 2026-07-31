# Enable Gemini AI Job-Description Generation

The application already contains a server-side Gemini REST integration. The API key must be stored in Streamlit Community Cloud secrets and must never be committed to GitHub.

Add these root-level secrets:

```toml
GEMINI_API_KEY = "paste-your-google-ai-studio-api-key"
GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_TIMEOUT_SECONDS = "25"
```

Keep all existing PostgreSQL and admin secrets unchanged. After saving, reboot the Streamlit app. The sidebar should show `JD generator: Gemini AI + fallback`.

The workflow is AI-first: Gemini generates a structured role-specific description for any meaningful job title. If quota, network, or provider errors occur, the broad local generator is used so resume analysis still works.
