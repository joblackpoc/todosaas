from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from subscriptions.models import Plan, Subscription

User = get_user_model()


class AccountsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.free_plan = Plan.objects.create(name="Free", price=0, task_limit=5)
        self.subscription = Subscription.objects.create(
            user=self.user, plan=self.free_plan
        )

    def test_dashboard_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth_app/dashboard.html")
        self.assertContains(response, "Free")
        self.assertNotContains(response, "Quick Stats")

    def test_signup_view(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "somepassword123",
                "password2": "somepassword123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_view(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "testuser",
                "password": "12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_logout_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse("_auth_user_id" in self.client.session)
