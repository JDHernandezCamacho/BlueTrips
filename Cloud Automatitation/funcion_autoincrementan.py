from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from google.cloud import bigquery, storage

# Función para cargar datos desde GCS a BigQuery
def load_data_to_bigqueryp(**kwargs):
    # Configura el cliente de BigQuery y GCS
    bq_client = bigquery.Client()
    gcs_client = storage.Client()

    # Define el nombre del bucket y la tabla en BigQuery
    bucket_name = 'us-central1-composerurbangr-6160ff9c-bucket'
    dataset_id = 'DatasetU'
    table_id = 'Autoincremento_ejemplo_3'

    # Obtiene el bucket de GCS
    bucket = gcs_client.bucket(bucket_name)

    # Lista de archivos en el bucket
    blobs = bucket.list_blobs(prefix='data/')  # Ajusta el prefijo si es necesario

    # Carga cada archivo en BigQuery
    for blob in blobs:
        if blob.name.endswith('.csv'):
            uri = f"gs://{bucket_name}/{blob.name}"
            load_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=1,
                field_delimiter=",",
                write_disposition="WRITE_APPEND",
            )
            load_job = bq_client.load_table_from_uri(
                uri,
                f"{dataset_id}.{table_id}",
                job_config=load_config
            )
            load_job.result()  # Espera a que el trabajo se complete
            print(f"Loaded {blob.name} to BigQuery.")
            
            # Mover el archivo a la carpeta "processed/"
            new_blob_name = f"processed/{blob.name.split('/')[-1]}"
            new_blob = bucket.rename_blob(blob, new_blob_name)
            print(f"Moved {blob.name} to {new_blob_name}.")

    print("Data loaded to BigQuery successfully.")

# Define el DAG
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
}

dag = DAG(
    dag_id='load_data_to_bigquery_pyt',
    default_args=default_args,
    schedule_interval=None,  # Usar sensor o Cloud Function para activar automáticamente
)

# Tarea para cargar datos desde GCS a BigQuery usando PythonOperator
load_data_task = PythonOperator(
    task_id='load_data_to_bq',
    python_callable=load_data_to_bigqueryp,
    dag=dag,
)

# Define la secuencia de tareas
load_data_task
