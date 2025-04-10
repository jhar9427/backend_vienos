

import tempfile
import ctd
import gsw
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from scipy.optimize import curve_fit
from datetime import datetime
from rest_framework import status,viewsets
from rest_framework.response import Response
from rest_framework.decorators import action 
from .models import Measurements, ProfileData
from  metadata.models import QualityFactors
from  variables.models import Variables
from .serializers import CombinedDataSerializer, MeasurementsSerializer, ProfileDataSerializer, StationNameSerializer
from .utils import extract_information
from .calculateClyna import halocline, picnocline, thermocline

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
      


class MeasurementsAndTeos(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='data_teos')
    def get_variable_name(self, request):
        try:
            variables_request = request.data.get('variables_names', [])
            
            if not variables_request:
                return Response({'error': 'No se proporcionaron variables'}, status=status.HTTP_400_BAD_REQUEST)
            
            variable_names = list(Variables.objects.filter(name__in=variables_request)
                                  .values_list('name', flat=True))
            variable_data = {name: [] for name in variable_names}
            
            profile_data = ProfileData.objects.filter(variable__name__in=variable_names)
            
            for entry in profile_data.values('variable__name', 'depth_marker', 'variable_value'):
                variable_name, depth, value = entry['variable__name'], entry['depth_marker'], entry['variable_value']
                variable_data[variable_name].append({'depth_marker': depth, 'value': value})
            
            data = []
            depths = sorted({entry['depth_marker'] for entries in variable_data.values() for entry in entries})
            has_temp_sal = 'Temperature' in variable_data and 'Salinity' in variable_data
        
            if has_temp_sal:
                temp_data = sorted(variable_data['Temperature'], key=lambda x: x['depth_marker'])
                sal_data = sorted(variable_data['Salinity'], key=lambda x: x['depth_marker'])
                depth_map = {entry['depth_marker']: entry['value'] for entry in sal_data}
            
                for temp_entry in temp_data:
                    depth = round(temp_entry['depth_marker'], 2)
                    temp_value = temp_entry['value']
                    sal = depth_map.get(temp_entry['depth_marker'])
            
                    if sal is not None:
                        data.append({
                            'depth': depth,
                            'potential_temperature': round(gsw.pt0_from_t(sal, temp_value, depth), 2),
                            'salinity': round(sal, 2),
                            'density': round(gsw.sigma0(sal, temp_value), 2)
                        })
            else:
                for depth in depths:
                    entry_data = {'depth': depth}
                    for var in variables_request:
                        values_at_depth = [entry['value'] for entry in variable_data.get(var, []) if entry['depth_marker'] == depth]
                        entry_data[var] = values_at_depth if values_at_depth else None
                    data.append(entry_data)
                        
            response_status = status.HTTP_200_OK if data else status.HTTP_204_NO_CONTENT
            message = "Data retrieved successfully" if response_status == status.HTTP_200_OK else "No data found for the given parameters"
            
            return Response({
                "data": CombinedDataSerializer(data, many=True).data,
            }, status=response_status)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            
            coordinates=Measurements.objects.filter(name=station_name).values('latitude','longitude')

            for entry in coordinates:
                 coordinates_data={
                      'latitude':entry['latitude'],
                      'longitude':entry['longitude']
                      }

            variables = Variables.objects.filter(name__in=variables_names, sensor__measurement__name=station_name)

            if variables.count() < len(variables_names):
                return Response({'error': 'No se encontraron todas las variables especificadas'}, status=status.HTTP_404_NOT_FOUND)

            data = []
            variable_data = {name: [] for name in variables_names}

            profile_data = ProfileData.objects.filter(variable__in=variables, timestamp__date=date)

            for entry in profile_data.values('variable__name', 'depth_marker', 'variable_value'):
                variable_name, depth, value = entry['variable__name'], entry['depth_marker'], entry['variable_value']
                variable_data[variable_name].append({'depth_marker': depth, 'value': value})

            depths = sorted({entry['depth_marker'] for entries in variable_data.values() for entry in entries})

            for depth in depths:
                entry_data = {'depth': depth}
                for var in variables_names:
                    values_at_depth = [entry['value'] for entry in variable_data.get(var, []) if entry['depth_marker'] == depth]
                    entry_data[var] = values_at_depth[0] if values_at_depth else None
                data.append(entry_data)

            

            if 'Temperature' in variables_names and 'Salinity' in variables_names:
                df = pd.DataFrame(data).rename(columns={
                           'depth': 'pres',
                           'Salinity': 'SP',
                           'Temperature': 't'
                     }).sort_values(by='pres').dropna(subset=['pres', 'SP', 't']).reset_index(drop=True)

                lon,lat =coordinates_data['latitude'],coordinates_data['longitude']
            

                if lat is None or lon is None:
                    return Response({'error': 'Se requiere latitud y longitud para calcular SA y CT'}, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    df['SA'] = gsw.SA_from_SP(df['SP'].values, df['pres'].values, lon, lat)
                    df['CT'] = gsw.CT_from_t(df['SA'].values, df['t'].values, df['pres'].values)
                    df['sigma0'] = gsw.sigma0(df['SA'],df['CT'])
                    

                    print(df['CT'])
                
                    df = df.rename(columns={
                        'SA': 'asal',
                        'CT': 'ctemp'
                       
                    })
                   
                    
                    pres_mtd, temp_mtd, pres_mld, temp_mld, r2, _, _, _ = thermocline(df)
                    inicio_haloclina, fin_haloclina, modelo= halocline(df)
                    inicio_picnoclina, fin_picnoclina, modelo=picnocline(df)

                    print(f'prof_inicial:{inicio_haloclina},final:{fin_haloclina}')
                    print(f'prof_ini_pic:{inicio_picnoclina},prof_fin_pic:{fin_picnoclina}')
                
                except Exception as e:
                    print("Error en cálculo de SA/CT:", e)
                    pres_mtd = temp_mtd = pres_mld = temp_mld = r2 = None
                    

            response_status = status.HTTP_200_OK if any(entry.get(var) for entry in data for var in variables_names) else status.HTTP_204_NO_CONTENT
            message = "Datos recuperados con éxito" if response_status == status.HTTP_200_OK else "No se encontraron datos para los parámetros proporcionados"

            return Response({
                "coordinates":coordinates_data,
                "data": CombinedDataSerializer(data, many=True).data,
                "thermocline_model": {
                    "pres_mtd": pres_mtd,
                    "temp_mtd": temp_mtd,
                    "pres_mld": pres_mld,
                    "temp_mld": temp_mld,
                    "r2": r2,
                    
                } if pres_mld is not None else None,
            }, status=response_status)
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



