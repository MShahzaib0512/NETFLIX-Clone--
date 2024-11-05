from django.urls import path
from .views import (
    index,
    register,
    login_user,
    registration,
    payment,
    success,
    failed,
    subscribe,
    fetch_subscription_plans,
)

urlpatterns = [
    # Home page
    path('', index, name='index'),

    # User registration
    path('register', register, name='register'),
    path('registration', registration, name='registration'),

    # User login
    path('login_user', login_user, name='login_user'),

    # Subscription plans
    path('fetch_subscription_plans/<str:email>', fetch_subscription_plans, name='fetch_subscription_plans'),

    # Payment process
    path('payment/<str:cid>', payment, name='payment'),

    # Subscription management
    path('subscribe/', subscribe, name='subscribe'),

    # Success and failure pages
    path('success', success, name='success'),
    path('failed', failed, name='failed'),
]
