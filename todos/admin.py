from django.contrib import admin

from .models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'completed', 'created_at', 'due_date')
    list_filter = ('completed', 'created_at', 'due_date')
    search_fields = ('title',)
