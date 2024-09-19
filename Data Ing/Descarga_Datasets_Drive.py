# Importar librerías
import gdown
import os 
import requests 
import pandas as pd 


# ---------------------- SCRIPT PARA DESCARGAR LOS DATOS DE LOS DATASETS APORTADOS POR HENRY  ----------------------

# Nombre de la carpeta donde se guardarán los archivos descargados
Data  = 'Datos Extraídos'

# Crear la carpeta 'Data' si no existe
os.makedirs(Data, exist_ok= True)

# Lista de archivos a descargar con sus IDs y nombres
files = [
    {'id' : '1p73YBd4tjQF2au4IAo99FY6nq-JJX2t-', 'name' : 'Alternative Fuel Vehicles US.csv'},
    {'id' : '1yWpl9nGxQkoylCU_SA0LFwCAENyftGH2', 'name' : 'ElectricCarData_Norm.csv'},
    {'id' : '1znjBC1zmJ_s2nsLlmxSlyLwkcZLFGEod', 'name' : 'ElectricCarData_Clean.csv'},
    {'id' : '18hzPaVttvyo8QyuC-jVSrN1-jkCnCIpW', 'name' : 'Light Duty Vehicles.csv'},
    {'id' : '1tEsF-bZYqqBM2gjcHxdbzVeip-90wHFM', 'name' : 'Vehicle Fuel Economy Data.csv'},
    {'id' : '1tHyZ1OVgJNhcn-rsJk3Ynrd7m58oc0CJ', 'name' : 'Taxi+_zone_lookup.csv'}
    ]


# Descargar archivos de Google Drive
for file in files:
    # Construir la URL para descargar el archivo desde Google Drive usando su ID
    url = f"https://drive.google.com/uc?id={file['id']}"
    
    # Construir la ruta completa para guardar el archivo en la carpeta 'Data'
    file_path = os.path.join(Data, file['name'])
    
    # Descargar el archivo usando gdown
    gdown.download(url, file_path, quiet=False)
    
    



# ---------------------- SCRIPT PARA DESCARGAR LOS DATOS DE LA CALIDAD DEL AIRE ----------------------

# Definir la URL de la API de datos
url = 'https://data.cityofnewyork.us/resource/c3uy-2p5r.json'

# Parámetros de consulta para limitar el número de registros
params =  {
    '$limit' : 18030            
}   

# Realizar la solicitud HTTP GET a la URL con los parámetros especificados
response = requests.get(url, params= params)

# Crear la carpeta de destino si no existe
# dest_folder = 'Datos Extraídos'
if not os.path.exists(Data):
    os.makedirs(Data)

# Verificar si la solicitud fue exitosa (código de estado HTTP 200)
if response.status_code == 200:
    
    # Convertir la respuesta JSON a un objeto Python (lista de diccionarios)              
    data = response.json()
    # Crear un DataFrame de pandas a partir de los datos JSON   
    df = pd.DataFrame(data)
    
    # Construir la ruta completa del archivo CSV donde se guardarán los datos
    file_path = os.path.join(Data, 'Datos_Calidad_Aire.csv')
    # Guardar el DataFrame en un archivo CSV en la ruta especificada    
    df.to_csv(file_path, index = False)
    
else:
    # Imprimir un mensaje de error si la solicitud no fue exitosa   
    print(f'Error: {response.status_code}')