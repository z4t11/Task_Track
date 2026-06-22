import json
import os
import time
from typing import Any, Dict, List, Optional

from django.utils import timezone

from .ai_service import _build_prompt as _build_ai_prompt
from ..models import Todo, ScheduledPlan

GROQ_API_URL = os.environ.get('GROQ_API_URL')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')


def _build_schedule_prompt(user, todos: List[Todo]) -> str:
    # Build a clear prompt describing tasks and desired output JSON schema
    tasks = []
    for t in todos:
        tasks.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'estimated_duration_minutes': t.estimated_duration_minutes,
            'energy_level': t.energy_level,
            'weather_sensitive': t.weather_sensitive,
            'preferred_weather': t.preferred_weather,
            'ai_category': t.ai_category,
        })

    prompt = (
        "You are an assistant that creates an ordered schedule for a user's tasks. "
        "Return a JSON object with keys: 'today', 'tomorrow', 'upcoming', and 'explanations'. "
        "Each day should be an array of tasks with keys: id, title, scheduled_date (ISO), start_time (HH:MM), duration_minutes, reason. "
        "Explanations should map task id to a short rationale.\n\n"
        f"Tasks: {json.dumps(tasks)}\n\n"
        "Constraints: do not change task titles or ids. Prioritize overdue tasks first. Prefer scheduling weather-sensitive tasks when preferred_weather includes 'sunny'. Keep total scheduled minutes per day under 12 hours (720 minutes)."
    )
    return prompt


def _validate_schedule(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    for key in ('today', 'tomorrow', 'upcoming', 'explanations'):
        if key not in obj:
            return False
    return True


def generate_schedule_for_user(user, max_retries: int = 3, backoff: float = 1.0) -> Optional[Dict]:
    todos = list(Todo.objects.filter(user=user))
    if not todos:
        return None

    prompt = _build_schedule_prompt(user, todos)
    if GROQ_API_URL is None or GROQ_API_KEY is None:
        return None

    import requests

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GROQ_API_KEY}',
    }
    payload = {
        'prompt': prompt,
        'max_tokens': 1200,
        'temperature': 0.0,
    }

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            body = resp.json()

            # Try to extract JSON result
            if isinstance(body, dict) and 'result' in body:
                result = body['result']
                if isinstance(result, str):
                    parsed = json.loads(result)
                else:
                    parsed = result
            else:
                parsed = body

            if _validate_schedule(parsed):
                # Add explanations to each item for easier template rendering
                explanations_map = parsed.get('explanations', {})
                for section in ('today', 'tomorrow', 'upcoming'):
                    if section in parsed and isinstance(parsed[section], list):
                        for item in parsed[section]:
                            item['reason'] = explanations_map.get(str(item.get('id', '')), '')
                
                # persist
                plan = ScheduledPlan.objects.create(
                    user=user,
                    data=parsed,
                    explanation=json.dumps(explanations_map),
                )
                return {'plan': parsed, 'saved_as': plan.id}

            last_exc = RuntimeError('Invalid schedule response')
        except Exception as exc:
            last_exc = exc
        time.sleep(backoff * attempt)

    return None