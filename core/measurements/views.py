

from collections import Counter, defaultdict
import tempfile
import ctd
import gsw
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from datetime import datetime
from rest_framework import status,viewsets
from rest_framework.response import Response
from rest_framework.decorators import action 
from .models import Measurements, ProfileData
from  metadata.models import QualityFactors
from  variables.models import Variables
from .serializers import CombinedDataSerializer, MeasurementsSerializer, ProfileDataSerializer, SectionDataResponseSerializer, StationNameSerializer, ThermoclineSerializer, HaloclineSerializer, PicnoclineSerializer  
from .utils import extract_information
from .services.oceangrafy import Structures

# Create your views here.

class MeasurementsView(viewsets.ModelViewSet):
    serializer_class = MeasurementsSerializer

    def get_queryset(self):
        return Measurements.objects.all()  # O una consulta personalizada

    

class ProfileDataView(viewsets.ModelViewSet):
    serializer_class=ProfileDataSerializer

    def get_queryset(self):
        return ProfileData.objects.all()
    

class UpFileloadCnv(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_cnv(self, request):
        file = request.FILES.get('file')
        if not file or not file.name.endswith('.cnv'):
            return Response({"error": "Se requiere un archivo CNV válido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.cnv') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            data = extract_information(temp_file_path)
            cast = ctd.from_cnv(temp_file_path)
            data_time = data.get('system_upload_time', datetime.now())
            station_name = data.get('station_number', 'Desconocida')
            pressure = cast.index
            
            variables_list = [
                ('Temperature', 'tv290C'), ('Salinity', 'sal00'), ('Conductivity', 'c0mS/cm'),
                ('Oxygen', 'sbeox0ML/L'), ('pH', 'ph'), ('Fluorescence', 'flECO-AFL'),
                ('Nitrogen Saturation', 'n2satMg/L'), ('Density', 'density00'),
                ('Descent Rate', 'dz/dtM'), ('Sound Velocity', 'svCM'), ('Flag', 'flag')
            ]
            
            variables_dict = {name: cast.get(key) for name, key in variables_list}

            quality_factor = QualityFactors.objects.filter(id=1).first()
            if not quality_factor:
                return Response({"error": "Factor de calidad con ID 1 no encontrado"}, status=status.HTTP_400_BAD_REQUEST)
            
            for variable_name, values in variables_dict.items():
                variable = Variables.objects.filter(sensor__measurement__name=station_name, name=variable_name).first()

                print(variable)
                if not variable:
                    print(f"Variable '{variable_name}' no encontrada para la estación '{station_name}'.")
                    continue

                for i, value in enumerate(values):
                    if pd.isna(value):
                        continue
                    
                    depth_marker = pressure[i] if i < len(pressure) else 0.0
                    try:
                        profile_data = ProfileData(
                            process_descriptor=0.0,
                            quality_factor=quality_factor,
                            depth_marker=depth_marker,
                            variable=variable,
                            variable_value=float(value),
                            timestamp=data_time
                        )
                        profile_data.full_clean()
                        profile_data.save()
                    except Exception as e:
                        print(f"Error guardando ProfileData para '{variable_name}': {e}")
            
            return Response({"status": "Archivo procesado exitosamente"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"Error procesando archivo CNV: {e}")
            return Response({"error": f"Error al procesar el archivo: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class MeasurementFilterDepth(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='depth')
    def filter_variable_depth(self, request):
        try:
    
            variable_names = request.data.get('variable_names', [])
            date_str = request.data.get('date')
            station_name = request.data.get('station_name')
            values_depths = request.data.get('value_depth', [])

            if not variable_names or not station_name or not date_str:
                return Response({'error': 'Falta una o más variables necesarias'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido, debe ser YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        
            variables = Variables.objects.filter(name__in=variable_names, sensor__measurement__name=station_name)
            if variables.count() < len(variable_names):
                return Response({'error': 'No se encontraron todas las variables con los nombres y estación proporcionados'}, status=status.HTTP_404_NOT_FOUND)

            profile_data = ProfileData.objects.filter(
                variable__in=variables,
                timestamp__date=date,
                depth_marker__in=values_depths
            ).values('variable__name', 'depth_marker', 'variable_value')


            variable_data = {var.name: {} for var in variables}
            for entry in profile_data:
                variable_name, depth, value = entry['variable__name'], entry['depth_marker'], entry['variable_value']
                depth_str = str(int(depth)) if depth.is_integer() else str(depth)
                variable_data[variable_name].setdefault(depth_str, []).append(value)

            
            combined_data = [
                {'depth': depth, **{var: variable_data[var].get(str(depth), []) for var in variable_names}}
                for depth in values_depths
            ]

            
            if any(entry.get(var, []) for entry in combined_data for var in variable_names):
                response_status = status.HTTP_200_OK
                message = "Datos recuperados correctamente"
            else:
                response_status = status.HTTP_204_NO_CONTENT
                message = "No se encontraron datos para los parámetros dados"

            return Response({
                "data": CombinedDataSerializer(combined_data, many=True).data,
            }, status=response_status)

        except Exception as e:
            return Response({"error": f"Ha ocurrido un error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
class Calcaulae(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='data')
    def get_variable_name(self, request):
        try:
            variables_names= request.data.get('variables_names', [])
            
            if not variables_names:
                return Response({'error': 'No se proporcionaron variables'}, status=status.HTTP_400_BAD_REQUEST)
            
            variables=Variables.objects.filter(name__in=variables_names).values_list('name', flat=True).distinct()
            profiles=ProfileData.objects.filter(variable__name__in=variables).select_related('variable')

            variable_data = defaultdict(list)
            for entry in profiles:
                variable_name, depth, value = entry.variable.name, entry.depth_marker, entry.variable_value
                variable_data[variable_name].append({'depth': depth, 'value': value})
            
            data = []
            
            has_temp_sal = 'Temperature' in variable_data and 'Salinity' in variable_data
        
            if has_temp_sal:
                temp_data = sorted(variable_data['Temperature'], key=lambda x: x['depth'])
                sal_data = sorted(variable_data['Salinity'], key=lambda x: x['depth'])
                depth_map = {entry['depth']: entry['value'] for entry in sal_data}
            
                for temp_entry in temp_data:
                    depth = round(temp_entry['depth'], 2)
                    temp_value = temp_entry['value']
                    sal = depth_map.get(temp_entry['depth'])
            
                    if sal is not None:
                        data.append({
                            'depth': depth,
                            'potential_temperature': round(gsw.pt0_from_t(sal, temp_value, depth), 2),
                            'salinity': round(sal, 2),
                            'density': round(gsw.sigma0(sal, temp_value), 2)
                        })
            else:
                depth_data = defaultdict(dict)
                for var_name, entries in variable_data.items():
                    for entry in entries:
                        depth_data[entry['depth_marker']][var_name] = entry['value']

                print(depth_data)       
                
                data = [
                    {'depth': depth, **{var: depth_data[depth].get(var) for var in variables_names}}
                    for depth in sorted(depth_data.keys())
                ]
                        
            response_status = status.HTTP_200_OK if data else status.HTTP_204_NO_CONTENT
            message = "Data retrieved successfully" if response_status == status.HTTP_200_OK else "No data found for the given parameters"
            
            return Response({
                "data": CombinedDataSerializer(data, many=True).data,
            }, status=response_status)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MeasurementsAndTeos(viewsets.ViewSet): 
    @action(detail=False, methods=['post'], url_path='data_teos')
    def get_variable_name(self, request):
        try:
            variables_names = request.data.get('variables_names', [])
            if not variables_names:
                return Response({'error': 'No se proporcionaron variables'}, status=status.HTTP_400_BAD_REQUEST)
            
            variables = Variables.objects.filter(name__in=variables_names).values_list('name', flat=True).distinct()
            profiles = ProfileData.objects.filter(variable__name__in=variables).select_related('variable')

            variable_data = self._group_profiles(profiles)
            data, isopicna, water_types_detected = [], None, set()

            if 'Temperature' in variable_data and 'Salinity' in variable_data:
                data, sal_array, temp_array, sigma_array, water_types_detected = self._process_temp_sal(variable_data)

                if len(sal_array) >= 10:
                    isopicna = self._generate_isopycnal_grid(sal_array, temp_array, sigma_array)

            else:
                data = self._process_generic_variables(variable_data, variables_names)

            response_status = status.HTTP_200_OK if data else status.HTTP_204_NO_CONTENT

            return Response({
                "data": CombinedDataSerializer(data, many=True).data,
                "grid": isopicna,
                "types": self._get_water_type_definitions(water_types_detected) if water_types_detected else None,
            }, status=response_status)

        except Exception as e:
            return Response({"error": f"Ocurrió un error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _group_profiles(self, profiles):
        variable_data = defaultdict(list)
        for entry in profiles:
            variable_data[entry.variable.name].append({
                'depth': entry.depth_marker,
                'value': entry.variable_value
            })
        return variable_data

    def _process_temp_sal(self, variable_data):
        temp_data = sorted(variable_data['Temperature'], key=lambda x: x['depth'])
        sal_data = {round(entry['depth'], 2): entry['value'] for entry in variable_data['Salinity']}

        data, sal_array, temp_array, sigma_array, type_water = [], [], [], [], set()

        for temp_entry in temp_data:
            depth = round(temp_entry['depth'], 2)
            temp = temp_entry['value']
            sal = sal_data.get(depth)

            if sal is not None and temp is not None:
                pot_temp = round(gsw.pt0_from_t(sal, temp, depth), 2)
                density = round(gsw.sigma0(sal, temp), 4)

                data.append({
                    'depth': -depth,
                    'potential_temperature': pot_temp,
                    'salinity': round(sal, 2),
                })

                sal_array.append(sal)
                temp_array.append(pot_temp)
                sigma_array.append(density)

                water_type = self._classify_water_type(sal, pot_temp)
                if water_type:
                    type_water.add(water_type)

        return data, sal_array, temp_array, sigma_array, type_water

    def _generate_isopycnal_grid(self, sal_array, temp_array, sigma_array):
        try:
            xi = np.linspace(min(sal_array), max(sal_array), 100)
            yi = np.linspace(min(temp_array), max(temp_array), 100)
            Xi, Yi = np.meshgrid(xi, yi)
            Zi = griddata((sal_array, temp_array), sigma_array, (Xi, Yi), method='linear')

            return {
                "sal_grid": xi.tolist(),
                "temp_grid": yi.tolist(),
                "density_grid": np.where(np.isnan(Zi), None, Zi).tolist(),
            }
        except Exception as e:
            return {"error": f"Error generando isopicnas: {str(e)}"}

    def _process_generic_variables(self, variable_data, variables_names):
        depth_data = defaultdict(dict)
        for var_name, entries in variable_data.items():
            for entry in entries:
                depth_data[entry['depth']][var_name] = entry['value']

        return [
            {'depth': -depth, **{var: depth_data[depth].get(var) for var in variables_names}}
            for depth in sorted(depth_data.keys())
        ]

    def _classify_water_type(self, sal, temp):
        if sal < 28 and 25 < temp < 28:
            return 'ACC'
        if 28 <= sal < 35 and 25 <= temp < 28:
            return 'AST'
        if 33.5 < sal <= 36 and 16 <= temp <= 25:
            return 'AES'
        if 34 <= sal <= 36 and 6 <= temp <= 16:
            return 'ASTSS'
        if 34 < sal <= 36 and temp < 6:
            return 'AAI'
        return None

    def _get_water_type_definitions(self, types_detected):
        water_types = {
            'ACC':   {'sal_min': 0,    'sal_max': 28,  'temp_min': 25, 'temp_max': 28},
            'AST':   {'sal_min': 28,   'sal_max': 35,  'temp_min': 25, 'temp_max': 28},
            'AES':   {'sal_min': 33.5, 'sal_max': 36,  'temp_min': 16, 'temp_max': 25},
            'ASTSS': {'sal_min': 34,   'sal_max': 36,  'temp_min': 6,  'temp_max': 16},
            'AAI':   {'sal_min': 34,   'sal_max': 36,  'temp_min': -2, 'temp_max': 6},
        }
        return [{"name": name, **water_types[name]} for name in types_detected if name in water_types]

class MeasurementsFilterStation(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path="station")
    def get_variable_station(self, request, **kwargs):
        try:
            variables_names = request.data.get('variables_names', [])
            date_str = request.data.get('date')
            station_name = request.data.get('station_name')

            if not (variables_names and station_name and date_str):
                return Response({'error': 'Verifique que las variables, la fecha y el nombre de la estación sean correctos'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido, debe ser YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
            
            coordinates = Measurements.objects.filter(name=station_name).values_list('latitude', 'longitude').first()

            if not coordinates:
                return Response({'error': 'Estación no encontrada'}, status=status.HTTP_404_NOT_FOUND)
            coordinates_data = {'latitude': coordinates[0], 'longitude': coordinates[1]}

            variables = Variables.objects.filter(name__in=variables_names, sensor__measurement__name=station_name).select_related('sensor__measurement')

            if variables.count() < len(variables_names):
                return Response({'error': 'No se encontraron todas las variables especificadas'}, status=status.HTTP_404_NOT_FOUND)

            profile_data = ProfileData.objects.filter(variable__in=variables, timestamp__date=date).select_related('variable')
    
            depth_data = defaultdict(dict)
            for entry in profile_data:
                variable_name = entry.variable.name  
                depth_marker = entry.depth_marker 
                variable_value = entry.variable_value  

                depth_data[depth_marker][variable_name] = variable_value
            
            data = [
                {'depth': depth, **{var: depth_data[depth].get(var) for var in variables_names}}
                for depth in sorted(depth_data.keys())
            ]

            thermocline, halocline, picnocline=self.structure_water(data,coordinates_data)  
                  

            response_status = status.HTTP_200_OK if any(entry.get(var) for entry in data for var in variables_names) else status.HTTP_204_NO_CONTENT
            return Response({
                "coordinates": coordinates_data,
                "data": CombinedDataSerializer(data, many=True).data,
                "thermocline": thermocline,
                "halocline":halocline,
                "picnocline":picnocline
            }, status=response_status)

        except Exception as e:
            return Response({'error': f'Ocurrió un error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def structure_water(self,data,coordinates_data):

            thermocline_data = None
            halocline_data = None
            picnocline_data = None

            first_data=data[0]
              
            if 'Temperature' in first_data and 'Salinity' in first_data:
                df = pd.DataFrame(data).rename(columns={
                    'depth':'pres',
                    'Salinity':'SP',
                    'Temperature':'t'
                }).sort_values(by='pres').dropna(subset=['pres', 'SP', 't']).reset_index(drop=True)

                lon, lat = coordinates_data.get('latitude'), coordinates_data.get('longitude')
                if lat is None or lon is None:
                    return Response({'error': 'Se requiere latitud y longitud para calcular SA y CT'}, status=status.HTTP_400_BAD_REQUEST)
            
                result =Structures(df, lat, lon)

                if result:
                    thermocline_data, halocline_data, picnocline_data = result['thermocline'],result['halocline'],result['picnocline']
                else:
                    thermocline_data = None
                    halocline_data = None
                    picnocline_data = None
                    
            return thermocline_data,halocline_data,picnocline_data      

class CalculateStructureStation(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='calculate_strcuture')
    def calaculate(self, request):
        try:
            data=request.data.get('data',[])
            coordinate=request.data.get('coordinates',[])

            if not  data or not coordinate:
                return Response({'error': 'Faltan datos o coordenadas'}, status=status.HTTP_400_BAD_REQUEST)
            
            thermocline_data = None
            halocline_data = None
            picnocline_data = None

            first_data=data[0]
              
            if 'Temperature' in first_data and 'Salinity' in first_data:
                df = pd.DataFrame(data).rename(columns={
                    'depth':'pres',
                    'Salinity':'SP',
                    'Temperature':'t'
                }).sort_values(by='pres').dropna(subset=['pres', 'SP', 't']).reset_index(drop=True)

                
                lon, lat = coordinate.get('latitude'), coordinate.get('longitude')
                if lat is None or lon is None:
                    return Response({'error': 'Se requiere latitud y longitud para calcular SA y CT'}, status=status.HTTP_400_BAD_REQUEST)
            
                result =Structures(df, lat, lon)

                if result:
                    thermocline_data, halocline_data, picnocline_data = result['thermocline'],result['halocline'],result['picnocline']
                else:
                    thermocline_data = None
                    halocline_data = None
                    picnocline_data = None

            return Response({
                "thermocline": ThermoclineSerializer(thermocline_data).data if thermocline_data else None,
                "halocline": HaloclineSerializer(halocline_data).data if halocline_data else None,
                "picnocline": PicnoclineSerializer(picnocline_data).data if picnocline_data else None,
                
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Ocurrió un error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
class MeasurementsList(viewsets.ViewSet):
    @action(detail=False, methods=['get'], url_path='list')
    def get_stations_name(self, request):
        try:
            station_name=Measurements.objects.values('name').distinct()
            serializer=StationNameSerializer(station_name,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error':'An error'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

class SeccionData(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='section')
    def get_seccion(self, request):
        try:
    
            variable_name = request.data.get('variable')
            station_names = request.data.get('stations_names', [])

            if not variable_name or not station_names:
                return Response(
                    {"error": "Se requiere 'variable' y 'stations_names'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if isinstance(station_names, str):
                station_names = [station_names]

            stations = Measurements.objects.filter(name__in=station_names).values('name', 'latitude', 'longitude')
            station_coords = {s['name']: (s['latitude'], s['longitude']) for s in stations}

            if not station_coords:
                return Response({'error': 'No se encontraron estaciones válidas.'}, status=status.HTTP_404_NOT_FOUND)

           
            variables = Variables.objects.filter(
                name=variable_name,
                sensor__measurement__name__in=station_coords.keys()
            ).select_related('sensor__measurement')

            if not variables.exists():
                return Response(
                    {"error": f"No se encontraron variables '{variable_name}' en las estaciones dadas."},
                    status=status.HTTP_404_NOT_FOUND
                )

            profiles = ProfileData.objects.filter(variable__in=variables).select_related('variable__sensor__measurement')

            if not profiles.exists():
                return Response({'error': 'No se encontraron datos de perfil.'}, status=status.HTTP_404_NOT_FOUND)

           
            latitudes, depths, values = [], [], []

            for profile in profiles:
                station_name = profile.variable.sensor.measurement.name
                coords = station_coords.get(station_name)
                if not coords:
                    continue

                latitudes.append(coords[0])
                depths.append(profile.depth_marker)
                values.append(profile.variable_value)

            if not latitudes:
                return Response({'error': 'No se pudieron agrupar datos válidos.'}, status=status.HTTP_404_NOT_FOUND)

            latitudes = np.array(latitudes)
            depths = np.array(depths)
            values = np.array(values)

            
            grid_latitudes, grid_depths = np.meshgrid(
                np.linspace(latitudes.min(), latitudes.max(), 400),
                np.linspace(depths.min(), depths.max(), 2000)
            )

            grid_values = griddata(
                (latitudes, depths),
                values,
                (grid_latitudes, grid_depths),
                method='linear'
            )

            grid_values_clean = np.where(np.isnan(grid_values), None, grid_values)
            
            response_data = {
                "x": grid_latitudes[0].tolist(),
                "y": grid_depths[:, 0].tolist(),
                "z": grid_values_clean.tolist()
            }

            serializer = SectionDataResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)

            return Response({"data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f"Ocurrió un error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)