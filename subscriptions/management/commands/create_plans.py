from django.core.management.base import BaseCommand
from subscriptions.models import Plan


class Command(BaseCommand):
    help = "Seeds the default pricing plans"

    def handle(self, *args, **kwargs):
        default_plans = [
            {"name": "Free", "stripe_price_id": "price_0", "price": 0, "task_limit": 5},
            {
                "name": "Standard",
                "stripe_price_id": "price_1QAVbyKFjfpndF9jFOJ2ad1k",
                "price": 5,
                "task_limit": 25,
            },
            {
                "name": "Professional",
                "stripe_price_id": "price_1QAVcjKFjfpndF9jJbkO0Vi4",
                "price": 10,
                "task_limit": 50,
            },
            {
                "name": "Enterprise",
                "stripe_price_id": "price_1QAVeHKFjfpndF9jcDBpv1uq",
                "price": 15,
                "task_limit": 1000,
            },
        ]

        for plan_data in default_plans:
            Plan.objects.get_or_create(**plan_data)

        self.stdout.write(self.style.SUCCESS("Successfully seeded pricing plans"))
