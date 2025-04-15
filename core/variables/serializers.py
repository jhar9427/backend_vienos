from rest_framework import serializers
from .models import Variables

class VariablesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variables
        fields = '__all__'

class VariableNameSerializer(serializers.Serializer):
    name=serializers.CharField()

class VariableUnitSerializer(serializers.Serializer):
    variable_name = serializers.CharField(max_length=50)
    unit = serializers.CharField(max_length=20)
