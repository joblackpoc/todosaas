from .models import Subscription, Plan


def get_user_plan(user):
    try:
        subscription = Subscription.objects.get(user=user)
        return subscription.plan.name
    except Subscription.DoesNotExist:
        return None


def user_has_feature(user, feature):
    plan = get_user_plan(user)
    if plan == "Enterprise":
        return True
    elif plan == "Professional":
        return feature != "overdue_tasks" and feature != "tasks_due_today"
    elif plan == "Standard":
        return feature in ["timer_and_date", "total_tasks", "completed_tasks"]
    else:
        return False
