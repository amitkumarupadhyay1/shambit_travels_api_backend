from django.contrib import admin
from .models import PricingRule

@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'value', 'is_percentage', 'target_package', 'is_active', 'active_from']
    list_filter = ['rule_type', 'is_percentage', 'is_active', 'active_from']
    search_fields = ['name', 'target_package__name']
    list_editable = ['is_active']
    date_hierarchy = 'active_from'
    
    fieldsets = (
        ('Rule Details', {
            'fields': ('name', 'rule_type', 'value', 'is_percentage')
        }),
        ('Targeting', {
            'fields': ('target_package',),
            'description': 'Leave empty to apply to all packages'
        }),
        ('Activation', {
            'fields': ('is_active', 'active_from', 'active_to')
        }),
    )