from rest_framework import serializers
from .models import PricingRule
from packages.serializers import PackageSerializer

class PricingRuleSerializer(serializers.ModelSerializer):
    target_package_name = serializers.CharField(source='target_package.name', read_only=True)
    
    class Meta:
        model = PricingRule
        fields = [
            'id', 'name', 'rule_type', 'value', 'is_percentage',
            'target_package', 'target_package_name', 'active_from', 
            'active_to', 'is_active'
        ]
    
    def validate(self, data):
        """
        Validate pricing rule data
        """
        # Ensure value is positive
        if data.get('value', 0) < 0:
            raise serializers.ValidationError("Value must be positive")
        
        # Validate percentage values
        if data.get('is_percentage', False) and data.get('value', 0) > 100:
            if data.get('rule_type') == 'DISCOUNT':
                raise serializers.ValidationError("Discount percentage cannot exceed 100%")
        
        # Validate date range
        active_from = data.get('active_from')
        active_to = data.get('active_to')
        if active_from and active_to and active_from >= active_to:
            raise serializers.ValidationError("Active from date must be before active to date")
        
        return data

class PricingBreakdownSerializer(serializers.Serializer):
    """
    Serializer for price breakdown response
    """
    base_experience_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    transport_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal_before_hotel = serializers.DecimalField(max_digits=10, decimal_places=2)
    hotel_multiplier = serializers.DecimalField(max_digits=4, decimal_places=2)
    subtotal_after_hotel = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_markup = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    applied_rules = serializers.ListField(child=serializers.DictField())