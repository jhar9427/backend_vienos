from rest_framework.viewsets import ModelViewSet
from .models import Equipments, MaintenancesDates, Settings
from .serializers import EquipmentsSerializer, MaintenancesDatesSerializer, SettingsSerializer

class EquipmentsView(ModelViewSet):
    queryset = Equipments.objects.all()
    serializer_class = EquipmentsSerializer

    # Personalizar la consulta de datos
    def get_queryset(self):
        return Equipments.objects.all()

    

class MaintenancesDatesView(ModelViewSet):
    queryset = MaintenancesDates.objects.all()
    serializer_class = MaintenancesDatesSerializer

class SettingsListView(ModelViewSet):
    queryset = Settings.objects.all()
    serializer_class = SettingsSerializer


