from django.urls import path
from . import views

urlpatterns = [
    path("", views.todo_list, name="todo_list"),
    path("create/", views.create_todo, name="create_todo"),
    path("edit/<int:pk>/", views.update_todo, name="update_todo"),
    path("delete/<int:pk>/", views.delete_todo, name="delete_todo"),
    path("status/<int:pk>/", views.update_todo_status, name="update_todo_status"),
]
