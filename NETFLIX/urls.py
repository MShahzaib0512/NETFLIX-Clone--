from django.urls import path
from .views import (
    index,
    register,
    plans,
    login_user,
    registration,
    payment,
    success,
    failed,
    subscribe,
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
    path('plans/<str:email>', plans, name='plans'),

    # Payment process
    path('payment/<str:cid>', payment, name='payment'),

    # Subscription management
    path('subscribe', subscribe, name='subscribe'),

    # Success and failure pages
    path('success', success, name='success'),
    path('failed', failed, name='failed'),
]
