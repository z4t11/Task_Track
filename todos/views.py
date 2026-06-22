from datetime import datetime

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import RegistrationForm, ProfileForm
from .models import Todo
from .services.planner_service import generate_plan_for_user
from .services.scheduler_service import generate_schedule_for_user


@login_required
def index(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        due_date = None
        due_date_str = request.POST.get('due_date', '').strip()
        if due_date_str:
            try:
                due_date = timezone.make_aware(datetime.fromisoformat(due_date_str))
            except ValueError:
                due_date = None

        if title:
            Todo.objects.create(user=request.user, title=title, due_date=due_date, description=description)
            return redirect('index')

    todos = Todo.objects.filter(user=request.user)
    return render(request, 'todos/index.html', {'todos': todos})


@login_required
def add_todo(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        due_date = None
        due_date_str = request.POST.get('due_date', '').strip()
        if due_date_str:
            try:
                due_date = timezone.make_aware(datetime.fromisoformat(due_date_str))
            except ValueError:
                due_date = None

        if title:
            Todo.objects.create(user=request.user, title=title, due_date=due_date, description=description)
            return redirect('index')

    return render(request, 'todos/add.html', {'is_add_page': True})


@login_required
def toggle(request, todo_id):
    todo = get_object_or_404(Todo, pk=todo_id, user=request.user)
    todo.completed = not todo.completed
    todo.save()
    return redirect('index')


@login_required
def delete_todo(request, todo_id):
    todo = get_object_or_404(Todo, pk=todo_id, user=request.user)
    if request.method == 'POST':
        todo.delete()
        return redirect('index')
    return render(request, 'todos/delete_confirm.html', {'todo': todo})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'todos/profile.html', {'form': form})


@login_required
def generate_plan(request):
    plan = generate_plan_for_user(request.user)
    # plan is a list of dicts with 'todo', 'score', 'reasons'
    return render(request, 'todos/plan.html', {'plan': plan})

@login_required
def ai_schedule(request):
    result = None
    error = None

    try:
        result = generate_schedule_for_user(request.user)

        # 🚨 guard clause
        if not result:
            raise ValueError("AI returned empty response")

        plan = result.get("plan", {})

        explanations = plan.get("explanations", {})

        for item in plan.get("today", []):
            item["reason"] = explanations.get(str(item.get("id")), "")

        for item in plan.get("tomorrow", []):
            item["reason"] = explanations.get(str(item.get("id")), "")

        result["plan"] = plan

    except Exception as e:
        error = str(e)

    return render(request, 'todos/ai_schedule.html', {
        'result': result,
        'error': error
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')