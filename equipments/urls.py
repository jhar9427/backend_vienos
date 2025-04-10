from django.urls import include,path
from rest_framework.routers import DefaultRouter

from .views import EquipmentsView, MaintenancesDatesView, SettingsListView


router=DefaultRouter()
router.register(r'equipments',EquipmentsView,basename='equipments')
router.register(r'maintenances-date',MaintenancesDatesView,basename='maintenancedate')
router.register(r'settings',SettingsListView,basename='setting')




urlpatterns = [
    
    
    path('',include(router.urls)),
    

]