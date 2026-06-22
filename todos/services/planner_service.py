from datetime import datetime, timezone
from typing import List, Dict

from django.utils import timezone as dj_timezone

from ..models import Todo


def score_task(todo: Todo, now=None) -> Dict:
    now = now or dj_timezone.now()
    score = 0.0
    reasons = []

    # Completed tasks should be lowest priority
    if todo.completed:
        reasons.append('Already completed')
        return {'todo': todo, 'score': -100.0, 'reasons': reasons}

    # Overdue gets highest boost
    if todo.due_date:
        if todo.due_date < now:
            score += 1000
            reasons.append('Overdue')
        else:
            # urgency proportional to proximity
            delta = (todo.due_date - now).total_seconds()
            days = delta / 86400.0
            # more urgent when fewer days left
            score += max(0, 500 - days * 50)
            if days < 1:
                reasons.append('Due within 24 hours')
            elif days < 3:
                reasons.append('Due within 3 days')
    else:
        reasons.append('No due date')

    # AI provided priority score
    try:
        score += float(todo.ai_priority_score or 0) * 10.0
        if todo.ai_priority_score:
            reasons.append('AI priority score')
    except Exception:
        pass

    # Longer tasks earlier (weight)
    if todo.estimated_duration_minutes:
        score += min(todo.estimated_duration_minutes / 10.0, 50)
        reasons.append('Estimated duration')

    # Weather-sensitive tasks get small boost (placeholder)
    if todo.weather_sensitive:
        score += 5
        reasons.append('Weather sensitive')

    # Newer tasks slightly lower priority
    age_hours = (now - todo.created_at).total_seconds() / 3600.0
    score += max(0, 10 - min(age_hours / 24.0, 10))

    return {'todo': todo, 'score': score, 'reasons': reasons}


def generate_plan_for_user(user) -> List[Dict]:
    todos = Todo.objects.filter(user=user)
    scored = [score_task(t) for t in todos]
    scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)
    return scored_sorted
