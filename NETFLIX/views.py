from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login as auth_login
from django.conf import settings
from djstripe.models import Price, Customer, Subscription, APIKey
import stripe
import json
from .models import *

key = APIKey.objects.filter(livemode=False).first()
# print(key.secret)
stripe.api_key = key.secret
# Create your views here.

def index(request):
    """Render the homepage."""
    return render(request, 'index.html')

def plans(request, email):
    """Render the subscription plans page."""
    monthly_plans = SubscriptionPlan.objects.prefetch_related('descriptions').filter(interval='monthly')
    yearly_plans = SubscriptionPlan.objects.prefetch_related('descriptions').filter(interval='yearly')
    plans = Price.objects.all()  # Getting all prices from DJ Stripe

    context = {
        'plan': plans,
        'monthly_plans': monthly_plans,
        'yearly_plans': yearly_plans,
        'STRIPE_TEST_PUBLIC_KEY': settings.STRIPE_TEST_PUBLIC_KEY,
        'email': email
    }

    return render(request, 'plans.html', context)

def login_user(request):
    """Handle user login."""
    if request.method == 'POST':
        uname = request.POST['username']
        passw = request.POST['password']
        user = authenticate(username=uname, password=passw)
        
        if user is not None:
            auth_login(request, user)
            return redirect('success')
        else:
            return render(request, "failed.html")

    return render(request, 'login.html')

def register(request):
    """Handle user registration."""
    # Debug: Check Stripe API Key
    print("Stripe API Key:", stripe.api_key)

    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username')

        # Validate input
        if not email or not password or not username:
            return render(request, 'index.html', {'error': 'All fields are required.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'index.html', {'error': 'Username already taken. Please choose another.'})

        try:
            # Create a new user in Django
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
        except Exception as e:
            print(f"Failed to create user: {e}")
            return render(request, 'index.html', {'error': 'An unexpected error occurred while creating your account.'})

        # Create Stripe customer and sync with DJ Stripe
        try:
            if not stripe.api_key:
                raise ValueError("Stripe API key is missing. Please check your configuration.")

            stripe_customer = create_stripe_customer(email=email)
            print(" customer created successfully ",stripe_customer)

        except ValueError as e:
            print(f"Configuration error: {e}")
            return render(request, 'index.html', {'error': 'Configuration error. Please contact support.'})
        
        except Exception as e:
            print(f"Failed to create Stripe customer: {e}")
            return render(request, 'index.html', {'error': 'Failed to create a customer in Stripe.'})

        return redirect('plans', email=email)


    return render(request, 'registration_form.html')

def registration(request):
    """Render the registration confirmation page."""
    if request.method == 'POST':
        email = request.POST['email']
        return render(request, "registration.html", {'email': email})

    return render(request, 'registration.html')

def payment(request, cid):
    """Render the payment page."""
    price_id = cid
    return render(request, 'payment.html', {
        'STRIPE_TEST_PUBLIC_KEY': settings.STRIPE_TEST_PUBLIC_KEY, 
        'price_id': price_id
    })

def create_stripe_customer(email):
    try:
        stripe_customer = stripe.Customer.create(email=email)
        return Customer.sync_from_stripe_data(stripe_customer)
    except Exception as e:
        print(f"Stripe error: {e}")
        return None

@login_required
@require_POST
def subscribe(request):
    """Handle subscription creation."""
    print("In subscribe view")

    try:
        data = json.loads(request.body)
        price_id = data.get('price_id')
        email = data.get('email')

        if not price_id or not email:
            return JsonResponse({'error': 'Missing required fields: price_id or email.'}, status=400)

        # Fetch or create Stripe customer
        stripe_customer = Customer.objects.filter(email=email).first()
        if not stripe_customer:
            stripe_customer = create_stripe_customer(email)
            if not stripe_customer:
                return JsonResponse({'error': 'Failed to create Stripe customer.'}, status=400)

        # Create checkout session
        print("Stripe customer:", stripe_customer)
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=request.build_absolute_uri(reverse('login_user')),
                cancel_url=request.build_absolute_uri(reverse('failed')),
                customer=stripe_customer.id,
            )
            return JsonResponse({'session_id': checkout_session.id})
        except stripe.error.StripeError as e:
            print(f"Stripe API error: {e}")
            return JsonResponse({'error': 'Failed to create checkout session with Stripe.'}, status=500)

    except (ValueError, json.JSONDecodeError) as e:
        print(f"JSON Error: {e}")
        return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return JsonResponse({'error': 'Failed to create subscription session.'}, status=500)


def failed(request):
    """Render the payment failure page."""
    return render(request, "failed.html", {'message': "Payment failed"})

def success(request):
    """Render the payment success page."""
    return render(request, "success.html")
