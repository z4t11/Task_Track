import threading
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Todo
from .services.ai_service import analyze_task

logger = logging.getLogger(__name__)


def _analyze_in_thread(todo_id: int):
    try:
        todo = Todo.objects.get(pk=todo_id)
    except Todo.DoesNotExist:
        return
    try:
        analyze_task(todo)
    except Exception as e:
        logger.exception('AI analysis failed for todo %s: %s', todo_id, e)


@receiver(post_save, sender=Todo)
def todo_post_save(sender, instance: Todo, created: bool, **kwargs):
    # Trigger AI analysis asynchronously so requests aren't blocked.
    # Only analyze when created or when core fields changed.
    thread = threading.Thread(target=_analyze_in_thread, args=(instance.pk,))
    thread.daemon = True
    thread.start()
