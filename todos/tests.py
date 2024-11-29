from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Todo
from subscriptions.models import Plan, Subscription
from datetime import date

User = get_user_model()


class TodosTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.free_plan = Plan.objects.create(name="Free", price=0, task_limit=5)
        self.pro_plan = Plan.objects.create(
            name="Professional", price=10, task_limit=25
        )
        self.subscription = Subscription.objects.create(
            user=self.user, plan=self.free_plan
        )
        self.todo = Todo.objects.create(user=self.user, title="Test Todo")

    def test_todo_model(self):
        self.assertEqual(str(self.todo), "Test Todo")
        self.assertFalse(self.todo.completed)

    def test_todo_list_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("todo_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todos/todo_list.html")
        self.assertContains(response, "Test Todo")
        self.assertNotContains(response, 'id="live-time"')

    def test_create_todo_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(reverse("create_todo"), {"title": "New Todo"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Todo.objects.filter(title="New Todo").exists())

    def test_create_todo_with_dates(self):
        self.subscription.plan = self.pro_plan
        self.subscription.save()
        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            reverse("create_todo"),
            {
                "title": "Todo with Dates",
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
        )
        self.assertEqual(response.status_code, 302)
        todo = Todo.objects.get(title="Todo with Dates")
        self.assertEqual(todo.start_date, date(2023, 1, 1))
        self.assertEqual(todo.end_date, date(2023, 1, 31))

    def test_update_todo_status(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(reverse("update_todo_status", args=[self.todo.id]))
        self.assertEqual(response.status_code, 302)
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.completed)

    def test_delete_todo(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(reverse("delete_todo", args=[self.todo.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Todo.objects.filter(id=self.todo.id).exists())
