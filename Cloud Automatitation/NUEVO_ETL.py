from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from datetime import datetime, timedelta
import gdown
import os
import requests
import pandas as pd
from google.cloud import storage
import re 
import dbfread  
from dbfread import DBF
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import shutil
import zipfile
from selenium.webdriver.chrome.options import Options






storage_client = storage.Client()
# Nombre del bucket y las rutas
BUCKET_NAME = 'us-central1-composer-urban--74a38dd0-bucket'
DATA_DIR = 'data/Datos_Extraídos'
TRANSFORMED_DATA_DIR = 'data/Datos_Transformados'
BUCKET_PATH = f'gs://{BUCKET_NAME}/{DATA_DIR}'
BUCKET = storage_client.bucket(BUCKET_NAME)

def upload_to_gcs(local_file_path, gcs_path):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_file_path)

def DescargarArchivos(**kwargs):
    
    
    # --------------------------------------------- DESCARGAR ARCHIVOS HENRY (DRIVE) ---------------------------------------------
    files = [
        {'id': '1yWpl9nGxQkoylCU_SA0LFwCAENyftGH2', 'name': 'ElectricCarData_Norm.csv'},
        {'id': '1tEsF-bZYqqBM2gjcHxdbzVeip-90wHFM', 'name': 'Vehicle_Fuel_Economy_Data.csv'},
    ]

    for file in files:
        url = f"https://drive.google.com/uc?id={file['id']}"
        output = os.path.join('/tmp', file['name'])
        gdown.download(url, output, quiet=False)
        # Cargar archivo a Google Cloud Storage
        upload_to_gcs(output, f'{DATA_DIR}/{file["name"]}')
        
        if file['name'].endswith('.dbf'):
            csv_output = os.path.join('/tmp', file['name'].replace('.dbf', '.csv'))
            output = csv_output  # Actualiza el nombre del archivo a CSV

        # Cargar archivo a Google Cloud Storage
        gcs_path = f'{DATA_DIR}/{os.path.basename(output)}'
        print(f'Cargando archivo: {output} a {gcs_path}')
        upload_to_gcs(output, gcs_path)

        
    # --------------------------------------------- DESCARGAR ARCHIVOS IMAGENES (DRIVE) ---------------------------------------------

    files_personal = [
        {'id' : '1VjkSV1_zHN4r1piD_odoT4FP8eUgQ7gj', 'name' : 'Electric_Alternative_Fuel_Charging.csv'},
        {'id' : '1fwEeRxLKvfJeTKltdOfy3MAvaErGwaa7', 'name' : 'CarImages.csv'},
        {'id' : '1U_5EgwzB5g9gnS0FKDXse_pNQJ0cPt1E', 'name' : 'ElectricCarData_Clean.csv'},
        {'id' : '1o_1e4QlZukrVKaYdP8PNYr_hpDgwvYUh', 'name' : 'Airports_Yellow_Trips_5_2024.csv'},
        {'id' : '1sepw774ICMgfRvMVGpFh-Qh0gYXo6LEm', 'name' : 'Airports_Yellow_Trips_6_2024.csv'},
        {'id' : '1g8gEoaYIRLGVtFz4D8Rid6KkSJskbsRk', 'name' : 'AirQualityJunio.csv'},
        {'id' : '1Qu6ProXCzxIrCNHXFxTENgU8ASpdUCLJ', 'name' : 'Locations.csv'}
    ]
    
    for files2 in files_personal:
        url_personal = f"https://drive.google.com/uc?id={files2['id']}"    
        output_personal = os.path.join('/tmp', files2['name'])
        gdown.download(url_personal, output_personal, quiet=False)
        upload_to_gcs(output_personal, f'{DATA_DIR}/{files2["name"]}')
    
    
    
    # --------------------------------------------- DESCARGAR ARCHIVOS CALIDAD AIRE (API) ---------------------------------------------
    
    url = 'https://data.cityofnewyork.us/resource/c3uy-2p5r.json'
    params = {'$limit': 18030}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        file_path = os.path.join('/tmp', 'Datos_Calidad_Aire.csv')
        df.to_csv(file_path, index=False)
        # Cargar archivo a Google Cloud Storage
        upload_to_gcs(file_path, f'{DATA_DIR}/Datos_Calidad_Aire.csv')
    else:
        print(f'Error: {response.status_code}')
        
        

def listar_archivos(BUCKET_NAME, DATA_DIR):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=DATA_DIR)
    archivos = [blob.name for blob in blobs if blob.name.endswith('.csv')]
    return archivos

def ManejoValoresNulos(df):
    columnas_numericas = df.select_dtypes(include=['number']).columns
    if df[columnas_numericas].isnull().any().any():
        df[columnas_numericas] = df[columnas_numericas].fillna(0)
        print(f"Valores nulos en columnas numéricas reemplazados por 0 en {columnas_numericas}")

    columnas_texto = df.select_dtypes(include=['object']).columns
    if df[columnas_texto].isnull().any().any():
        df[columnas_texto] = df[columnas_texto].fillna('Sin Dato')
        print(f"Valores nulos en columnas de texto reemplazados por 'Sin Dato' en {columnas_texto}")


# def ManejoTiposDatos(df):
#     for column in df.columns:
#         if df[column].dtype == 'int64':
#             df[column] = df[column].astype('int32')
#         if df[column].dtype == 'float64':
#             df[column] = df[column].astype('float32')


def ManejoFilasDuplicadas(df):
    
    if df.duplicated().any():
        df.drop_duplicates(keep='first', inplace=True)

    else: 
        print('No se encontraron duplicados')
        

        
def process_generic(processing_function, **kwargs):
    archivos = listar_archivos(BUCKET_NAME, DATA_DIR)
    for archivo in archivos:
        local_file_path = f'/tmp/{archivo.split("/")[-1]}'
        gcs_path = f'{DATA_DIR}/{archivo.split("/")[-1]}'
        
        print(f'Downloading {gcs_path} to {local_file_path}')
        blob = storage.Client().bucket(BUCKET_NAME).blob(gcs_path)
        blob.download_to_filename(local_file_path)
        
        print(f'Reading {local_file_path}')
        df = pd.read_csv(local_file_path)
        
        print(f'Applying processing function to {local_file_path}')
        processing_function(df)
        
        local_file_transformed_path = f'/tmp/transformed_{archivo.split("/")[-1]}'
        print(f'Saving transformed file to {local_file_transformed_path}')
        df.to_csv(local_file_transformed_path, index=False)
        
        gcs_transformed_path = f'{TRANSFORMED_DATA_DIR}/{archivo.split("/")[-1]}'
        print(f'Uploading transformed file to {gcs_transformed_path}')
        upload_to_gcs(local_file_transformed_path, gcs_transformed_path)



def process_data_manejo_valores_nulos(**kwargs):
    process_generic(ManejoValoresNulos, **kwargs)

# def process_data_manejo_tipos_datos(**kwargs):
#     process_generic(ManejoTiposDatos, **kwargs)

def process_data_manejo_filas_duplicadas(**kwargs):
    process_generic(ManejoFilasDuplicadas, **kwargs)

def load_data_to_bigquery(**kwargs):
     dataset_id = 'urban-green-solutions.DatasetU'
     archivos = listar_archivos(BUCKET_NAME, TRANSFORMED_DATA_DIR)

     for archivo in archivos:
         gcs_path = f'{TRANSFORMED_DATA_DIR}/{archivo.split("/")[-1]}'
         table_id = f'{dataset_id}.{archivo.split("/")[-1].replace(".csv", "").replace(".", "_")}'

         # Crear una instancia del operador GCSToBigQueryOperator
         load_task = GCSToBigQueryOperator(
             task_id=f'load_{archivo.split("/")[-1].replace(".csv", "").replace(".", "_")}',
             bucket=BUCKET_NAME,
             source_objects=[gcs_path],
             destination_project_dataset_table=table_id,
             source_format='CSV',
             skip_leading_rows=1,  # Ajusta según si tienes encabezados
             autodetect=True,  # Permite la detección automática de esquemas
             write_disposition='WRITE_TRUNCATE',  # Reemplaza la tabla existente
             dag=kwargs['dag']
         )
         load_task.execute(context=kwargs)

