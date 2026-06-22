from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone


class Todo(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='todos',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    due_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True, default='')

    estimated_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    ai_category = models.CharField(max_length=128, null=True, blank=True)

    ENERGY_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    energy_level = models.CharField(
        max_length=10,
        choices=ENERGY_LEVEL_CHOICES,
        null=True,
        blank=True
    )

    weather_sensitive = models.BooleanField(default=False)
    preferred_weather = models.JSONField(null=True, blank=True)

    BEST_TIME_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('night', 'Night'),
        ('any', 'Any'),
    ]
    best_time_of_day = models.CharField(
        max_length=16,
        choices=BEST_TIME_CHOICES,
        null=True,
        blank=True
    )

    ai_priority_score = models.FloatField(default=0.0)
    planned_date = models.DateTimeField(null=True, blank=True)
    last_ai_analysis = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < timezone.now()

    @property
    def due_in(self):
        if not self.due_date:
            return None

        delta = self.due_date - timezone.now()

        if delta.total_seconds() < 0:
            return "Overdue"

        if delta.days >= 1:
            return f"{delta.days} day(s) left"

        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m left"

        return f"{minutes}m left"


class ScheduledPlan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scheduled_plans',
    )

    name = models.CharField(max_length=200, default="AI Schedule")
    created_at = models.DateTimeField(auto_now_add=True)

    # THIS is where AI output goes
    data = models.JSONField(null=True, blank=True)

    explanation = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at:%Y-%m-%d}"
