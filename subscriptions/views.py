import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from .models import Plan, Subscription
from django.contrib.auth import get_user_model


stripe.api_key = settings.STRIPE_SECRET_KEY
User = get_user_model()


def pricing(request):
    plans = Plan.objects.all().order_by("price")
    current_plan = None

    if request.user.is_authenticated:
        current_subscription = Subscription.objects.filter(user=request.user).first()
        current_plan = current_subscription.plan if current_subscription else None

        if request.method == "POST":
            new_plan_id = request.POST.get("plan_id")
            new_plan = Plan.objects.get(id=new_plan_id)

            if new_plan.price == 0:
                current_subscription.plan = new_plan
                current_subscription.save()
                messages.success(
                    request,
                    f"You have been successfully downgraded to the {new_plan.name} plan.",
                )
                return redirect("pricing")
            else:
                return redirect("create_checkout_session", plan_id=new_plan.id)

        context = {
            "plans": plans,
            "current_plan": current_plan,
            "stripe_public_key": settings.STRIPE_PUBLISHABLE_KEY,
            "user_authenticated": request.user.is_authenticated,
        }
        return render(request, "subscriptions/pricing.html", context)


@login_required
def create_checkout_session(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    domain = "http://127.0.0.1:8000"
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": plan.stripe_price_id,
                "quantity": 1,
            }
        ],
        mode="subscription",
        success_url=f"{domain}{reverse('subscription_success')}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=domain + reverse("subscription_cancel"),
        client_reference_id=str(request.user.id),
    )
    request.session["checkout_session_id"] = checkout_session.id
    return JsonResponse({"sessionId": checkout_session.id})


@login_required
def subscription_success(request):
    session_id = request.GET.get("session_id")
    stored_session_id = request.session.get("checkout_session_id")
    if session_id == stored_session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            stripe_subscription_id = session.subscription
            stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            stripe_price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
            plan = Plan.objects.get(stripe_price_id=stripe_price_id)
            Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    "plan": plan,
                    "stripe_subscription_id": stripe_subscription_id,
                    "active": True,
                },
            )
            del request.session["checkout_session_id"]
            messages.success(request, "Your subscription was successful!")
        except Plan.DoesNotExist:
            messages.error(request, "The selected plan does not exist.")
            return HttpResponse(status=404, content="Plan not found.")
        except Subscription.DoesNotExist:
            messages.error(request, "Subscription could not be created or updated.")
            return HttpResponse(status=404, content="Subscription not found.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(
                status=500,
                content="An error occurred while processing your subscription.",
            )
    else:
        messages.error(
            request, "Invalid session ID. Your subscription could not be confirmed."
        )

    return redirect("dashboard")


@login_required
def subscription_cancel(request):
    request.session.pop("checkout_session_id", None)
    messages.info(request, "Your subscription process was cancelled.")
    return redirect("pricing")


def handle_subscription_updated(stripe_subscription):
    try:
        subscription = Subscription.objects.get(
            stripe_subscription_id=stripe_subscription["id"]
        )
        plan = Plan.objects.get(
            stripe_price_id=stripe_subscription["items"]["data"][0]["price"]["id"]
        )
        subscription.plan = plan
        subscription.active = stripe_subscription["status"] == "active"
        subscription.save()
    except Subscription.DoesNotExist:
        return HttpResponse(status=404, content="Subscription not found.")
    except Plan.DoesNotExist:
        return HttpResponse(status=404, content="Plan not found.")
    except Exception as e:
        return HttpResponse(
            status=500,
            content=f"An error occurred while updating the subscription: {str(e)}",
        )


def handle_subscription_deleted(stripe_subscription):
    try:
        subscription = Subscription.objects.get(
            stripe_subscription_id=stripe_subscription["id"]
        )
        subscription.active = False
        subscription.save()
    except Subscription.DoesNotExist:
        return HttpResponse(status=404, content="Subscription not found.")
    except Exception as e:
        return HttpResponse(
            status=500,
            content=f"An error occurred while deleting the subscription: {str(e)}",
        )


@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400, content="Invalid payload or signature.")

    if event["type"] == "customer.subscription.updated":
        handle_subscription_updated(event["data"]["object"])
    elif event["type"] == "customer.subscription.deleted":
        handle_subscription_deleted(event["data"]["object"])

    return HttpResponse(status=200)
