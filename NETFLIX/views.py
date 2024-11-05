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
from django.contrib import messages
from .decorator import *
from .models import *

key = APIKey.objects.filter(livemode=False).first()
# print(key.secret)
stripe.api_key = key.secret
# Create your views here.

def index(request):
    """Render the homepage."""
    return render(request, 'index.html')

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
            messages.error(request,"Error! invalid Email/password")
            return redirect("login_user")

    return render(request, 'login.html')

def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username')
        
        if not email or not password or not username:
            return render(request, 'index.html', {'error': 'All fields are required.'})
        
        if User.objects.filter(email=email).exists():
            messages.error(request,"user with the email already exists")
            return redirect('register')
        if User.objects.filter(username=username).exists():
            messages.error(request,"user with the username already exists")
            return redirect('register')
        if len(str(password)) < 8:
            messages.error(request,"your password must at least contains 8 characters")
            return redirect('register')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
        except Exception as e:
            print(f"Failed to create user: {e}")
            return render(request, 'index.html', {'error': 'An unexpected error occurred while creating your account.'})

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

        return redirect('fetch_subscription_plans', email=email)


    return render(request, 'registration.html')

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

def subscribe(request):
    """Handle subscription creation."""
    print("In subscribe view")

    try:
        if request.method == 'POST':
            email = request.POST.get('email')
            price_id = request.POST.get('price_id')

            print(price_id)
            if not price_id or not email:
                messages.error(request,'Missing required fields: price_id or email.')
                return redirect ('fetch_subscription_plans')
            
            customers=stripe.Customer.list()
            stripe_customer = Customer.objects.filter(email=email).first()
            for customer in customers:
                print(customer.email)
                if customer.email==email:
                    stripe_customer=customer    
            
            if not stripe_customer:
                stripe_customer = create_stripe_customer(email)
                if not stripe_customer:
                    return redirect(request,'Failed to create Stripe customer.')

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
                return redirect(checkout_session.url)
            except stripe.error.StripeError as e:
                # print(f"Stripe API error: {e}")
                # print(price_id)
                messages.error(request,'Failed to create checkout session with Stripe.')
                return redirect('fetch_subscription_plans')

    except Exception as e:
        print(f"Error creating checkout session: {e}")
        messages.error(request,'Failed to create subscription session.')
        return redirect('fetch_subscription_plans')

def failed(request):
    """Render the payment failure page."""
    return render(request, "failed.html", {'message': "Payment failed"})
@login_required(login_url="login_user")
@subscription_required
def success(request):
    """Render the payment success page."""
    return render(request, "success.html")

def fetch_subscription_plans(request,email):
    try:
        products = stripe.Product.list(limit=100)
        subscription_plans = []

        for product in products.data:
            prices = stripe.Price.list(product=product.id)

            for price in prices.data:
                subscription_plans.append({
                    'id': price.id,  
                    'product_name': product.name,
                    'amount': price.unit_amount / 100, 
                    'currency': price.currency,  
                    'interval': price.recurring.interval,  
                    'description': product.description,  
                    'price_id': price.id,  
                })

        return render(request, "stripe_plans.html", {'subscription_plans': subscription_plans, 'email':email})

    except stripe.error.StripeError as e:
        messages.error(request, f"An error occurred: {e.user_message}")
        return redirect('login_user')
