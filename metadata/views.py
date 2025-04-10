from rest_framework import viewsets
from .models import CecoldoCodes, Coasts, Departments, Disciplines, MeasurementUnits, ProcessingLevels, QualityFactors, SamplingRates
from .serializers import CecoldoCodesSerializer, CoastsSerializer, DepartmentsSerializer, DisciplinesSerializer, MeasurementUnitsSerializer, ProcessingLevelsSerializer, QualityFactorsSerializer, SamplingRatesSerializer

# ViewSets simplificados
class DisciplinesView(viewsets.ModelViewSet):
    queryset = Disciplines.objects.all()
    serializer_class = DisciplinesSerializer

class DepartmentsView(viewsets.ModelViewSet):
    queryset = Departments.objects.all()
    serializer_class = DepartmentsSerializer

class CoastsView(viewsets.ModelViewSet):
    queryset = Coasts.objects.all()
    serializer_class = CoastsSerializer

class MeasurementUnitsView(viewsets.ModelViewSet):
    queryset = MeasurementUnits.objects.all()
    serializer_class = MeasurementUnitsSerializer

class ProcessingLevelsView(viewsets.ModelViewSet):
    queryset = ProcessingLevels.objects.all()
    serializer_class = ProcessingLevelsSerializer

class SamplingRatesView(viewsets.ModelViewSet):
    queryset = SamplingRates.objects.all()
    serializer_class = SamplingRatesSerializer

class CecoldoCodesView(viewsets.ModelViewSet):
    queryset = CecoldoCodes.objects.all()
    serializer_class = CecoldoCodesSerializer

class QualityFactorsView(viewsets.ModelViewSet):
    queryset = QualityFactors.objects.all()
    serializer_class = QualityFactorsSerializer
