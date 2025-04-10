from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CecoldoCodesView, CoastsView, DepartmentsView, DisciplinesView, 
    MeasurementUnitsView, ProcessingLevelsView, QualityFactorsView, SamplingRatesView
)

# Configurar router para ViewSets
router = DefaultRouter()
router.register(r'disciplines', DisciplinesView)
router.register(r'departments', DepartmentsView)
router.register(r'coasts', CoastsView)
router.register(r'measurement-units', MeasurementUnitsView)
router.register(r'processing-levels', ProcessingLevelsView)
router.register(r'sampling-rates', SamplingRatesView)
router.register(r'cecoldo-codes', CecoldoCodesView)
router.register(r'quality-factors', QualityFactorsView)

urlpatterns = [
    path('', include(router.urls)),  # Incluir las rutas del router
]
