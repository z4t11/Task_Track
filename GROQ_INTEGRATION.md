Groq Integration — Configuration and Usage

Overview

This project integrates Groq AI calls to analyze tasks and generate schedules. To enable Groq features you must set two environment variables: `GROQ_API_URL` and `GROQ_API_KEY`.

Required environment variables

- `GROQ_API_URL`: Full endpoint URL for your Groq API (e.g. `https://api.groq.ai/v1/generate`).
- `GROQ_API_KEY`: Secret API key for authenticating with the Groq endpoint.

Recommended local setup

1. Create a `.env` file in the project root with the following content (do NOT commit `.env`):

```
GROQ_API_URL=https://your-groq-endpoint.example
GROQ_API_KEY=sk-xxxxx
```

2. Install optional helper package to auto-load `.env` into environment when Django starts (development only):

```bash
pip install python-dotenv
```

Then add to the top of `todo_project/settings.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

Security

- Never commit `GROQ_API_KEY` or `.env` to version control. Add `.env` to `.gitignore`.
- Use secret management in production (Azure Key Vault, AWS Secrets Manager, GCP Secret Manager, or environment variables in your deployment platform).
- Rotate API keys regularly and restrict their scope when possible.

Testing the integration

- Start the dev server with the environment variables set locally (PowerShell example):

```powershell
$Env:GROQ_API_URL = "https://your-groq-endpoint.example"
$Env:GROQ_API_KEY = "sk-xxxxx"
python manage.py runserver
```

- Log in and visit `/ai-schedule/` to generate and persist an AI schedule.
- For troubleshooting, check the server console for error messages from the HTTP calls.

API shape expectations

- The current `scheduler_service` expects the Groq response to be either a JSON object or a JSON object with a top-level `result` field containing a JSON string/object. The schedule JSON should contain the keys: `today`, `tomorrow`, `upcoming`, and `explanations`.

If your Groq deployment returns a different envelope, paste a sample response and I will adapt the parsing code.

Further improvements

- Add rate limiting, exponential backoff logging, and persistent job queue (Celery/RQ) for production workloads.
- Harden prompt and validation per your Groq model responses.

