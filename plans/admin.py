from datetime import timedelta
from django.contrib import admin
from .models import Plan, UserPlan
from django.utils import timezone

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'tool', 
        't1_projects_limit', 
        't2_projects_limit', 
        'is_unlimited', 
        'duration_days'
    )
    list_filter = ('tool', 'is_unlimited')
    search_fields = ('name',)
    
    # Make it easier to differentiate plan types
    list_display_links = ('name',)
    
    # Optional: Custom formatting for better readability
    def t1_projects_limit(self, obj):
        if obj.is_unlimited:
            return "∞ Unlimited"
        return obj.t1_projects_limit if obj.t1_projects_limit is not None else "—"
    t1_projects_limit.short_description = "T1 Projects Limit"

    def t2_projects_limit(self, obj):
        if obj.is_unlimited:
            return "∞ Unlimited"
        return obj.t2_projects_limit if obj.t2_projects_limit is not None else "—"
    t2_projects_limit.short_description = "T2 Projects Limit"




@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 
        'plan', 
        'active', 
        't1_projects_used', 
        't2_projects_used', 
        'start_date', 
        'end_date', 
        'expired',
        'remaining_days'
    )
    list_filter = ('active', 'plan__tool', 'plan')
    search_fields = ('customer__name', 'customer__email', 'plan__name')
    
    actions = ['activate_plan', 'deactivate_plan']

    def expired(self, obj):
        if not obj.end_date:
            return False
        return obj.end_date < timezone.now()
    expired.boolean = True
    expired.short_description = 'Expired'

    def remaining_days(self, obj):
        if not obj.end_date or not obj.active:
            return "—"
        delta = obj.end_date - timezone.now()
        if delta.days < 0:
            return "Expired"
        return f"{delta.days} days"
    remaining_days.short_description = "Remaining Days"

    @admin.action(description="Activate selected user plans")
    def activate_plan(self, request, queryset):
        for userplan in queryset:
            userplan.active = True
            userplan.start_date = timezone.now()
            userplan.end_date = timezone.now() + timedelta(days=userplan.plan.duration_days if userplan.plan else 30)
            userplan.t1_projects_used = 0
            userplan.t2_projects_used = 0
            userplan.save()
        self.message_user(request, "Selected user plans have been activated.")

    @admin.action(description="Deactivate selected user plans")
    def deactivate_plan(self, request, queryset):
        queryset.update(active=False)
        self.message_user(request, "Selected user plans have been deactivated.")  
    