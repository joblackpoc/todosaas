from django.db import models
from django.conf import settings


class Plan(models.Model):
    name = models.CharField(max_length=50)
    stripe_price_id = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    task_limit = models.IntegerField()

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
