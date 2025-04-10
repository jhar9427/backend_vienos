import re 
from datetime import datetime
import ctd


def extract_information(file_path):
    info = {
        'station_name': '',
        'cruise_name': '',
        'vessel_name': '',
        'station_number': '',
        'launch_date_time': '',
        'latitude': '',
        'longitude': '',
        'depth': '',
        'operator_name': '',
        'chief_of_departure': '',
        'system_upload_time': ''
    }

    with open(file_path, 'r') as file:
        content = file.read()

        # Regex patterns for each piece of information
        patterns = {
            #'station_name': r"Nombre del archivo:\s*(.*)",
            #'cruise_name': r"\*\* Nombre del crucero:\s*(.*)",
            #'vessel_name': r"\*\* Nombre de la embarcación y su indicativo:\s*(.*)",
            #'station_number': r"\*\* Estacion:\s*(.*)",
            'station_number': r"\*\* Número de estación:\s*(.*)",
            'launch_date_time': r"\*\* Fecha y hora de lanzamiento:\s*(.*)",
            'latitude': r"\*\* Latitud:\s*([0-9\.\-]+)",
            'longitude': r"\*\* Longitud:\s*([0-9\.\-]+)",
            #'depth': r"\*\* Profundidad de la zona \[ m\] :\s*(.*)",
            #'operator_name': r"\*\* Nombre del operador:\s*(.*)",
            #'chief_of_departure': r"\*\* Jefe de salida:\s*(.*)",
            'system_upload_time': r"System UpLoad Time = ([\w\s:]+)"
        }

        # Extract data using regex
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                info[key] = match.group(1).strip()

        
        # Convert launch date and time to specific format
        if info['launch_date_time']:
            try:
                launch_dt = datetime.strptime(info['launch_date_time'], "%d %b %Y, %H:%M:%S")
                info['launch_date_time'] = launch_dt.strftime("%Y-%m-%d %H:%M:%S.%f%z")
            except ValueError:
                print("Error al convertir la fecha y hora de lanzamiento.")
        # Optionally process the system upload time
        if info['system_upload_time']:
            try:
                upload_dt = datetime.strptime(info['system_upload_time'], "%b %d %Y %H:%M:%S")
                info['system_upload_time'] = upload_dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                print("Error al convertir la fecha y hora de subida del sistema.")
                
    return info



