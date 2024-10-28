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

# Set Stripe API Key
key = APIKey.objects.filter(livemode=False).first()
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
        stripe.api_key = key.secret
        try:
            if not stripe.api_key:
                raise ValueError("Stripe API key is missing. Please check your configuration.")

            print("Before creating Stripe customer, API Key:", stripe.api_key)
            stripe_customer = stripe.Customer.create(email=email)
            djstripe_customer = Customer.sync_from_stripe_data(stripe_customer)
            print(djstripe_customer.id)

        except ValueError as e:
            print(f"Configuration error: {e}")
            return render(request, 'index.html', {'error': 'Configuration error. Please contact support.'})
        
        except Exception as e:
            print(f"Failed to create Stripe customer: {e}")
            return render(request, 'index.html', {'error': 'Failed to create a customer in Stripe.'})

        return redirect(reverse('plans') + f"?email={email}")

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

@login_required
@require_POST
def subscribe(request):
    """Handle subscription creation."""
    # Parse JSON data from the request body
    try:
        data = json.loads(request.body)
        email = data.get('email')
        priceId=data.get('price_id')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)

        # Check if the user exists
        user = User.objects.filter(email=email).first()
        print(user)
        if user:
            stripe_customer = Customer.sync_from_stripe_data(user)
        else:
            # Create Stripe and DJ Stripe customer if user doesn't exist
            stripe.api_key = key.secret
            customer = stripe.Customer.create(email=email)
            print("This is customer that is created ",customer)
            stripe_customer = Customer.sync_from_stripe_data(customer)
            print("This is i want to sync from stripe  ",stripe_customer)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Failed to process subscription: {e}")
        print(f"Stripe API Key: {stripe.api_key}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

    # Create Stripe Checkout Session
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': priceId, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('success')) + '?status=success',
            cancel_url=request.build_absolute_uri(reverse('failed')) + '?status=failure',
            customer=stripe_customer.id
        )
        return JsonResponse({'sessionId': checkout_session.id})
    
    except Exception as e:
        print(f"Subscription creation failed: {e}")
        return JsonResponse({'error': 'Subscription creation failed'}, status=500)

def failed(request):
    """Render the payment failure page."""
    return render(request, "failed.html", {'message': "Payment failed"})

def success(request):
    """Render the payment success page."""
    return render(request, "success.html")
