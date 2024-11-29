from django.urls import path
from . import views

urlpatterns = [
    path("pricing/", views.pricing, name="pricing"),
    path(
        "create-checkout-session/<int:plan_id>/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path("success/", views.subscription_success, name="subscription_success"),
    path("cancel/", views.subscription_cancel, name="subscription_cancel"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
]
