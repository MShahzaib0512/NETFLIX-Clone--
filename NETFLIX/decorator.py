import stripe
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from djstripe.models import Customer, Subscription

def subscription_required(view_func):
  @wraps(view_func)
  def _wrap_view(request, *args, **kwargs):
      user = request.user
      email = user.email
      stripe_customer = Customer.objects.filter(email=email).first()
      if not stripe_customer:
          messages.error(request, "No Stripe customer found for this user.")
          return redirect('login_user')  
      subscriptions = stripe.Subscription.list(customer=stripe_customer.id).data
      has_active_subscription = any(
       sub.status in ["active", "trialing"] for sub in subscriptions
      )
      if has_active_subscription:
          return view_func(request, *args, **kwargs)
      else:
          messages.error(request, "Subscription has expired!")
          return redirect('login_user')  

  return _wrap_view
