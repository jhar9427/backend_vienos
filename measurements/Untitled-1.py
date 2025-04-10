class UpFileloadView(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='upload_cnv')
    def upload_cnv(self, request):
        print("Archivos recibidos:", request.FILES)  # <-- Debugging
        file = request.FILES.get('file')

        if not file:
           return Response({"error": "No se recibió ningún archivo"}, status=400)

        print("Archivo recibido:", file.name)  # <-- Debugging
        
        if not file or not file.name.endswith('.cnv'):
            return Response({"error": "Este no es un archivo CNV"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.cnv') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.seek(0)
                temp_file_path = temp_file.name
            
            print("Iniciando el proceso de carga del CNV...")
            data = extract_information(temp_file_path)
            cast = ctd.from_cnv(temp_file_path)
            dataTime = data['system_upload_time']
            station_name=data['station_number']
            print(dataTime)
            print(station_name)
            
            
            pressure = cast.index
            pressure = pressure

            variables_list=[
                 ('Temperature', 'tv290C'),
                 ('Salinity', 'sal00'),
                 ('Conductivity', 'c0mS/cm'),
                 ('Oxygen', 'sbeox0ML/L'),  # Puedes cambiarlo si necesitas 'sbeox0Mg/L'
                 ('pH', 'ph'),
                 ('Fluorescence', 'flECO-AFL'),  # Antes era 'flSP'
                 ('Nitrogen Saturation', 'n2satMg/L'),
                 ('Density', 'density00'),
                 ('Descent Rate', 'dz/dtM'),
                 ('Sound Velocity', 'svCM'),
                 ('Flag', 'flag')
                ]
            
            variables_dict={ name: cast.get(name_key) for name,name_key in variables_list}

            #print(variables_dict)

            try:
                quality_factor = QualityFactors.objects.get(id=1)  # Ajusta según sea necesario
            except QualityFactors.DoesNotExist:
                return Response({"error": "El factor de calidad con ID 1 no existe."}, status=status.HTTP_400_BAD_REQUEST)

            for variable_name, data in variables_dict.items():
                
                try:
                    varAll = Variables.objects.all()

                    if varAll.exists():
                        print(f"Se encontraron {varAll.count()} variables:")
                        for var in varAll:
                          print(f"- {var}")  # Asegúrate de que el modelo Variables tenga __str__ bien definido
                    else:
                      print("No hay datos en la tabla Variables.")

            
                    variable = Variables.objects.get(sensor__measurement__name=station_name, name=variable_name)
                      
                    for i, value in enumerate(data):
                        if pd.isna(value):
                            print(f"El valor en la fila {i} para {variable_name} es NaN o None")
                            continue
                        
                        
                        timestamp = datetime.now()  # Valor por defecto

                        print(f"Creando ProfileData con: process_descriptor=0.0, quality_factor={quality_factor}, depth_marker={pressure[i] if i < len(pressure) else 0.0}, variable={variable}, variable_value={float(value)}, timestamp={timestamp}")
                        
                        try:
                            profile_data = ProfileData(
                                process_descriptor=0.0,
                                quality_factor=quality_factor,
                                depth_marker=pressure[i] if i < len(pressure) else 0.0,
                                variable=variable,
                                variable_value=float(value),
                                timestamp=dataTime
                            )
                            profile_data.full_clean()  # Valida el objeto antes de guardarlo
                            profile_data.save()
                            print(f"ProfileData para la variable '{variable_name}' guardado exitosamente.")
                        except Exception as e:
                            print(f"Error al guardar ProfileData para la variable '{variable_name}': {str(e)}")
                except Variables.DoesNotExist:
                    print(f"Variable '{variable_name}' no existe.")
                except Exception as e:
                    print(f"Error al procesar variable '{variable_name}': {str(e)}")
            
            return Response({"status": "Archivo procesado exitosamente."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"Error al procesar el archivo: {str(e)}")
            return Response({"error": f"Ocurrió un error al procesar el archivo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

