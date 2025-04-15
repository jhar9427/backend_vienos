from rest_framework import serializers
from .models import Equipments,MaintenancesDates,Settings

class EquipmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipments
        fields = '__all__'

    
class MaintenancesDatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenancesDates
        fields = '__all__'        

class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'        