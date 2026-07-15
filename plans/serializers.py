# plans/serializers.py
from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    tool_display = serializers.CharField(source='get_tool_display', read_only=True)
    features_list = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            'id',
            'name',
            'tool',
            'tool_display',
            't1_projects_limit',
            't2_projects_limit',
            'is_unlimited',
            'duration_days',
            'price',
            'features',
            'features_list',
        ]
        read_only_fields = ['id', 'tool_display']
        
        
    def get_features_list(self, obj):
        if not obj.features:
            return []
        return [f.strip() for f in obj.features.split(",")] 