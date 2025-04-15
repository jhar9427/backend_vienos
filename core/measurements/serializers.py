from rest_framework import serializers
from .models import Measurements, ProfileData
from metadata.models import CecoldoCodes  # ✅ Importa el modelo correctamente
from metadata.serializers import CecoldoCodesSerializer  # ✅ Esto está bien

class MeasurementsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Measurements
        fields = '__all__'

class ProfileDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileData
        fields = ['depth_marker', 'variable_value']


class CombinedDataSerializer(serializers.Serializer):
    depth = serializers.FloatField()  # El campo 'depth' sigue siendo fijo, ya que siempre se espera
    # Las variables dinámicas se generarán a partir de los datos que se proporcionen

    def to_representation(self, instance):
        # Utiliza la representación original para el depth y luego itera sobre las variables restantes
        representation = {'depth': instance['depth']}
        
        # Añadir dinámicamente los otros valores variables (p. ej., temperatura, salinidad, etc.)
        for key, value in instance.items():
            if key != 'depth':  # Excluir 'depth' ya que se maneja por separado
                representation[key] = value
                
        return representation
    

class StationNameSerializer(serializers.Serializer):
    name=serializers.CharField()   