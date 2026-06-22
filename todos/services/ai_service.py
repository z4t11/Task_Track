import json
import os
import time
from typing import Any, Dict, Optional

from django.utils import timezone

from ..models import Todo


GROQ_API_URL = os.environ.get('GROQ_API_URL')
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


def _build_prompt(task: Todo) -> str:
    text = f"Analyze the following task and return a JSON object with keys: category, estimated_duration_minutes (int), energy_level (low|medium|high), weather_sensitive (true|false), preferred_weather (array of strings), best_time_of_day (morning|afternoon|evening|night|any).\nTask: {task.title}\nDescription: {task.description}\n"
    return text


def _validate_response(data: Dict[str, Any]) -> bool:
    if not isinstance(data, dict):
        return False
    required = ['category', 'estimated_duration_minutes', 'energy_level', 'weather_sensitive', 'preferred_weather', 'best_time_of_day']
    for k in required:
        if k not in data:
            return False
    return True


def analyze_task(task: Todo, max_retries: int = 3, backoff: float = 1.0) -> Optional[Dict[str, Any]]:
    """Call Groq to analyze `task` and persist AI fields on the model.

    This function is resilient: it retries on transient failures and validates
    the returned JSON before applying it to the model.
    """
    if GROQ_API_URL is None or GROQ_API_KEY is None:
        # API not configured; skip analysis
        return None

    prompt = _build_prompt(task)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GROQ_API_KEY}',
    }
    payload = {
        'prompt': prompt,
        'max_tokens': 300,
        'temperature': 0.0,
    }

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            import requests
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            # assume the API returns JSON body with string content we can parse
            body = resp.json()

            # Try to extract a structured result. Different Groq deployments may
            # return different shapes; attempt detection.
            if isinstance(body, dict) and 'result' in body and isinstance(body['result'], (dict, str)):
                result = body['result']
                if isinstance(result, str):
                    try:
                        parsed = json.loads(result)
                    except Exception:
                        parsed = None
                else:
                    parsed = result
            else:
                parsed = body

            if parsed and _validate_response(parsed):
                # persist to model
                task.ai_category = parsed.get('category')
                try:
                    task.estimated_duration_minutes = int(parsed.get('estimated_duration_minutes') or 0)
                except (TypeError, ValueError):
                    task.estimated_duration_minutes = None
                task.energy_level = parsed.get('energy_level')
                task.weather_sensitive = bool(parsed.get('weather_sensitive'))
                pref = parsed.get('preferred_weather')
                try:
                    # ensure it's JSON-serializable array
                    task.preferred_weather = pref if isinstance(pref, list) else json.loads(pref)
                except Exception:
                    task.preferred_weather = None
                task.best_time_of_day = parsed.get('best_time_of_day')
                task.last_ai_analysis = timezone.now()
                task.save(update_fields=['ai_category', 'estimated_duration_minutes', 'energy_level', 'weather_sensitive', 'preferred_weather', 'best_time_of_day', 'last_ai_analysis'])
                return parsed

            # invalid response -> raise to trigger retry or abort
            last_exc = RuntimeError(f'Invalid AI response: {body}')
        except Exception as exc:
            last_exc = exc

        # backoff before retrying
        time.sleep(backoff * attempt)

    # Log the last exception using Django logging if desired; skip here.
    return None
