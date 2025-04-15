
from rest_framework import serializers

from .models import CecoldoCodes, Coasts, Departments, Disciplines, MeasurementUnits, ProcessingLevels, QualityFactors, SamplingRates

class CoastsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coasts
        fields = '__all__'

class DepartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = '__all__'

class DisciplinesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disciplines
        fields = '__all__'


class MeasurementUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnits
        fields = '__all__'


class ProcessingLevelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingLevels
        fields = '__all__'

class SamplingRatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SamplingRates
        fields = '__all__'

class CecoldoCodesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CecoldoCodes
        fields = '__all__'


class QualityFactorsSerializer(serializers.ModelSerializer):
    class Meta:
        model=QualityFactors
        fields='__all__'                



