from django.db import models

# Subscription Plan Model
class SubscriptionPlan(models.Model):
    INTERVAL_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    PLAN_TYPE = [
        ('Basic', 'Basic'),
        ('Standard', 'Standard'),
        ('Premium', 'Premium'),
    ]
    
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE, default='Basic')  # Store selected plan type
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default='monthly')  # Add interval if needed
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    price_id=models.CharField(max_length=100, default=" ",null=True,blank=True)
    
    def __str__(self):
        return self.plan_type

# Description Model
class Description(models.Model):
    plan = models.ForeignKey(SubscriptionPlan, related_name='descriptions', on_delete=models.CASCADE, default=" ")
    content = models.CharField(max_length=50, blank=True, null=True)  # Description content

    def __str__(self):
        return f"Description for {self.plan}"  # This will call the __str__() of SubscriptionPlan
