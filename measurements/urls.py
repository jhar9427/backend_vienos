from django.urls import include,path
from rest_framework.routers import DefaultRouter

from .views import MeasurementsView, ProfileDataView, UpFileloadCnv , \
                   MeasurementFilterDepth, MeasurementsFilterStation, MeasurementsAndTeos, MeasurementsList


router=DefaultRouter()
router.register(r'measurements',MeasurementsView,basename='mesaurement')
router.register(r'profile-data',ProfileDataView,basename='profile')
router.register(r'file',UpFileloadCnv,basename='file')
router.register(r'filter',MeasurementFilterDepth,basename='filter_variables')
router.register(r'filter',MeasurementsAndTeos,basename='variables_teos')
router.register(r'filter', MeasurementsFilterStation, basename='filter_station')
router.register(r'station',MeasurementsList,basename='measurements_list')

urlpatterns = [
    path('',include(router.urls)),
]