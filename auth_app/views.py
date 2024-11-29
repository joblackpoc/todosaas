from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm

from .models import User
from subscriptions.models import Plan, Subscription
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from todos.models import Todo
from django.views.decorators.http import require_http_methods
import stripe
from django.conf import settings
from django.db.models import Q
from subscriptions.utils import user_has_feature
from datetime import timezone as dt_timezone


stripe.api_key = settings.STRIPE_SECRET_KEY


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "auth_app/signup.html"
    success_url = reverse_lazy("todo_list")

    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = form.save()
                login(self.request, user)

                free_plan, created = Plan.objects.get_or_create(
                    name="Free",
                    defaults={
                        "price": 0,
                        "task_limit": 10,
                        "stripe_price_id": "price_0",
                    },
                )

                Subscription.objects.create(user=user, plan=free_plan)
            return redirect(self.success_url)
        except Exception as e:
            messages.error(
                self.request, "An error occurred during signup. Please try again."
            )
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "There was an error with your submission. Please check the fields and try again.",
        )
        return self.render_to_response(self.get_context_data(form=form))


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()
                login(request, user)
                messages.success(
                    request, f"You have successfully logged in, {user.username}!"
                )
                return redirect("todo_list")
            except Exception as e:
                messages.error(
                    request, "An error occurred while logging in."
                )  # new line
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, "auth_app/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    try:
        username = request.user.username
        logout(request)
        messages.success(request, f"You have successfully logged out, {username}!")
    except Exception:  # new line
        messages.error(request, "An error occurred while logging out.")
    return redirect("home")


@login_required
def dashboard(request):
    try:
        subscription = Subscription.objects.get(user=request.user)
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timezone.timedelta(days=1)

        tasks_this_month = Todo.objects.filter(
            user=request.user, created_at__month=now.month, created_at__year=now.year
        ).count()

        tasks_limit = subscription.plan.task_limit
        tasks_left = max(0, tasks_limit - tasks_this_month)

        quick_stats = {}
        if user_has_feature(request.user, "total_tasks"):
            quick_stats["total_tasks"] = Todo.objects.filter(user=request.user).count()
        if user_has_feature(request.user, "completed_tasks"):
            quick_stats["completed_tasks"] = Todo.objects.filter(
                user=request.user, completed=True
            ).count()
        if user_has_feature(request.user, "pending_tasks"):
            quick_stats["pending_tasks"] = Todo.objects.filter(
                user=request.user, completed=False
            ).count()
        if user_has_feature(request.user, "tasks_due_today"):
            quick_stats["tasks_due_today"] = (
                Todo.objects.filter(user=request.user, completed=False)
                .filter(
                    Q(end_date__range=(today_start, today_end))
                    | Q(
                        end_date__isnull=True,
                        start_date__range=(today_start, today_end),
                    )
                )
                .count()
            )
        if user_has_feature(request.user, "overdue_tasks"):
            quick_stats["overdue_tasks"] = Todo.objects.filter(
                user=request.user, end_date__lt=today_start, completed=False
            ).count()

        context = {
            "subscription": subscription,
            "tasks_this_month": tasks_this_month,
            "tasks_left": tasks_left,
            "tasks_limit": tasks_limit,
            "quick_stats": quick_stats,
            "show_quick_stats": bool(quick_stats),
        }

        return render(request, "auth_app/dashboard.html", context)
    except Subscription.DoesNotExist:
        messages.error(request, "No subscription found. Please subscribe to a plan.")
        return redirect("home")
    except Exception as e:
        messages.error(request, "An error occurred while loading the dashboard.")
        return redirect("home")


@login_required
def cancel_subscription(request):
    if request.method == "POST":
        try:
            subscription = Subscription.objects.get(user=request.user)
            if subscription.stripe_subscription_id:
                try:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id, cancel_at_period_end=True
                    )
                    stripe_subscription = stripe.Subscription.retrieve(
                        subscription.stripe_subscription_id
                    )
                    end_date = timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_end, tz=dt_timezone.utc
                    )
                    request.session["subscription_end_date"] = end_date.isoformat()
                    messages.success(
                        request,
                        f"Your subscription has been cancelled. You can continue to use your current plan until {end_date.strftime('%B %d, %Y')}. "
                        "After this date, you will be moved to the Free plan.",
                    )
                except stripe.error.StripeError as e:
                    messages.error(request, f"An error occurred: {str(e)}")
            else:
                messages.warning(request, "No active subscription found.")
        except Subscription.DoesNotExist:
            messages.error(request, "You do not have an active subscription.")
        return redirect("dashboard")
    return redirect("dashboard")


@login_required
def delete_account(request):
    if request.method == "POST":
        try:
            user = request.user
            try:
                subscription = Subscription.objects.get(user=user)
                if subscription.stripe_subscription_id:
                    stripe.Subscription.delete(subscription.stripe_subscription_id)
            except Subscription.DoesNotExist:
                pass

            logout(request)
            user.delete()
            messages.success(request, "Your account has been successfully deleted.")
            return redirect("home")
        except Exception as e:
            messages.error(request, "An error occurred while deleting your account.")
    return redirect("dashboard")
