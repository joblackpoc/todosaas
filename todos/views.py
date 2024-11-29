from django.shortcuts import render, redirect, get_object_or_404
from .models import Todo
from django.core.paginator import Paginator
from .forms import TodoForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from subscriptions.models import Subscription
from subscriptions.utils import user_has_feature


@login_required
def todo_list(request):
    todos = Todo.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(todos, 7)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "show_timer_and_date": user_has_feature(request.user, "timer_and_date"),
    }

    return render(request, "todos/todo_list.html", context)


@login_required
def update_todo_status(request, pk):
    todo = get_object_or_404(Todo, pk=pk, user=request.user)
    todo.completed = not todo.completed
    todo.save()
    return redirect("todo_list")


@login_required
def create_todo(request):

    subscription = Subscription.objects.get(user=request.user)
    todos_this_month = Todo.objects.filter(
        user=request.user,
        created_at__month=timezone.now().month,
        created_at__year=timezone.now().year,
    ).count()

    if todos_this_month >= subscription.plan.task_limit:
        pricing_url = reverse("pricing")
        message = mark_safe(
            f"You've reached your monthly task limit. <a href='{pricing_url}'>Upgrade your plan</a> to add more tasks."
        )
        messages.warning(request, message)

        return redirect("todo_list")

    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user

            if user_has_feature(request.user, "start_end_date"):
                todo.start_date = request.POST.get("start_date") or None
                todo.end_date = request.POST.get("end_date") or None

            todo.save()
            messages.success(request, "New task created successfully!")
            return redirect("todo_list")
    else:
        form = TodoForm()

    context = {
        "form": form,
        "subscription": subscription,
        "todos_this_month": todos_this_month,
        "tasks_left": max(0, subscription.plan.task_limit - todos_this_month),
        "show_date_fields": user_has_feature(request.user, "start_end_date"),
    }

    return render(request, "todos/todo_form.html", context)


@login_required
def update_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk, user=request.user)
    if request.method == "POST":
        form = TodoForm(request.POST, instance=todo)
        if form.is_valid():
            form.save()
            return redirect("todo_list")
    else:
        form = TodoForm(instance=todo)
    return render(request, "todos/todo_form.html", {"form": form})


@login_required
def delete_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk, user=request.user)
    if request.method == "POST":
        todo.delete()
        return redirect("todo_list")
    return render(request, "todos/todo_confirm_delete.html", {"todo": todo})
