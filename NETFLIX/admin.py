from django.contrib import admin
from .models import SubscriptionPlan, Description

class DescriptionInline(admin.TabularInline):  
 model = Description
 extra = 1 
 min_num = 1 

class SubscriptionPlanAdmin(admin.ModelAdmin):
 list_display = ('plan_type', 'amount', 'interval') 
 inlines = [DescriptionInline] 

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
