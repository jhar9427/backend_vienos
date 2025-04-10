
from rest_framework import status,viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import VariableNameSerializer, VariableUnitSerializer, VariablesSerializer

from .models import Variables

# Create your views here.
class VariablesView(viewsets.ModelViewSet):
    queryset=Variables.objects.all()
    serializer_class=VariablesSerializer

    def get_queryset(self):
        return Variables.objects.all()
    
class VariablesListNames(viewsets.ViewSet):
   @action(detail=False, methods=['get'], url_path='names')
   def get_variable_name(self, request, **kwargs):
    try:
        variables_names = Variables.objects.values('name').distinct()
        serializer = VariableNameSerializer(variables_names, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f'An error occurred: {e}')
        return Response({"error": "An error occurred while retrieving variable names."}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class VariablesInfo(viewsets.ViewSet):
   @action(detail=False, methods=['post'], url_path='data')
   def get_units(self, request):
      try:
         variables_names=request.data.get('variables_names')
         station_name=request.data.get('station_name')
         print(variables_names)
         if not variables_names or not station_name:
          return Response({'error':'Falta una o mas variables'},status=400)
         
         try:
             variables=Variables.objects.filter(name__in=variables_names,sensor__measurement__name=station_name)
             print(f"Se encontraron la variables")
         except Exception as e:
              print(f'ha ocurrido un error en :{e}')   
              return Response({'error':'No se encontraron las variables'}) 
         
         data=[]
         for variable in variables:
             data.append({
                 'variable_name':variable.name,
                 'unit':variable.measurement_unit.symbol
                 })
         serializer=VariableUnitSerializer(data, many=True)  
         return Response(serializer.data, status=status.HTTP_200_OK)       
         
      except Exception as e:
            print(f"Ha occurido un error en :{e}")
            return Response({"error": "An error occurred while retrieving variable names."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


