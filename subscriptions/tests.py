from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Plan, Subscription
from .utils import user_has_feature
from unittest.mock import patch
from django.conf import settings

User = get_user_model()


class SubscriptionsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.free_plan = Plan.objects.create(
            name="Free", price=0, task_limit=5, stripe_price_id="price_0"
        )
        self.pro_plan = Plan.objects.create(
            name="Professional",
            price=10,
            task_limit=25,
            stripe_price_id="price_1234567890",
        )
        self.subscription = Subscription.objects.create(
            user=self.user, plan=self.free_plan
        )

    def test_plan_model(self):
        self.assertEqual(str(self.free_plan), "Free")
        self.assertEqual(self.free_plan.task_limit, 5)

    def test_subscription_model(self):
        self.assertEqual(str(self.subscription), "testuser - Free")
        self.assertTrue(self.subscription.active)

    def test_pricing_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("pricing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subscriptions/pricing.html")
        self.assertContains(response, "Free")
        self.assertContains(response, "Professional")

    def test_user_has_feature(self):
        self.assertFalse(user_has_feature(self.user, "start_end_date"))
        self.subscription.plan = self.pro_plan
        self.subscription.save()
        self.assertTrue(user_has_feature(self.user, "start_end_date"))

    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session(self, mock_create):
        mock_create.return_value = type("obj", (object,), {"id": "test_session_id"})

        self.client.login(username="testuser", password="12345")
        response = self.client.get(
            reverse("create_checkout_session", args=[self.pro_plan.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("sessionId", response.json())
        self.assertEqual(response.json()["sessionId"], "test_session_id")
        mock_create.assert_called_once_with(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": self.pro_plan.stripe_price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url="http://127.0.0.1:8000"
            + reverse("subscription_success")
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://127.0.0.1:8000" + reverse("subscription_cancel"),
            client_reference_id=str(self.user.id),
        )

    def test_stripe_keys(self):
        self.assertIsNotNone(settings.STRIPE_PUBLISHABLE_KEY)
        self.assertIsNotNone(settings.STRIPE_SECRET_KEY)
        self.assertTrue(settings.STRIPE_PUBLISHABLE_KEY.startswith("pk_"))
        self.assertTrue(settings.STRIPE_SECRET_KEY.startswith("sk_"))
