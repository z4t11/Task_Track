from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_todo, name='add_todo'),
    path('toggle/<int:todo_id>/', views.toggle, name='toggle'),
    path('delete/<int:todo_id>/', views.delete_todo, name='delete_todo'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/', views.profile, name='profile'),
    path('plan/', views.generate_plan, name='generate_plan'),
    path('ai-schedule/', views.ai_schedule, name='ai_schedule'),
     path('logout/', LogoutView.as_view(next_page='login'),name='logout'),
]
