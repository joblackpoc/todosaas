from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SignUpView, login_view, logout_view
from . import views

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="auth_app/password_reset_form.html"
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth_app/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth_app/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth_app/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("cancel-subscription/", views.cancel_subscription, name="cancel_subscription"),
    path("delete-account/", views.delete_account, name="delete_account"),
]
