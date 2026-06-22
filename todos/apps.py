from django.apps import AppConfig


class TodosConfig(AppConfig):
    name = 'todos'

    def ready(self):
        # import signals to ensure they are registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
