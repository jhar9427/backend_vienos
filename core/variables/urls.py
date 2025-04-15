from django.urls import include,path
from rest_framework.routers import DefaultRouter

from .views import VariablesListNames, VariablesInfo, VariablesView


router=DefaultRouter()
router.register(r'variables',VariablesView,basename='variables')
router.register(r'list',VariablesListNames,basename='names')
router.register(r'list', VariablesInfo,basename='units')


urlpatterns = [
    
    
    path('',include(router.urls)),
    

]