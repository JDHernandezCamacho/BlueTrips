from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
from NUEVO_ETL import DescargarArchivos, process_data_manejo_valores_nulos, load_data_to_bigquery



# Configuración predeterminada para el DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}




# Definición del DAG
dag = DAG(
    'ETL_DAG',
    default_args=default_args,
    description='Un DAG simple para un pipeline ETL',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 9, 1),
    catchup=False,
)

# Definición de las tareas
start_task = DummyOperator(task_id='start', dag=dag)
download_task = PythonOperator(task_id='download_data', python_callable=DescargarArchivos, dag=dag)
manejo_valores_nulos_task = PythonOperator(task_id='manejo_valores_nulos', python_callable=process_data_manejo_valores_nulos, dag=dag)
#manejo_tipos_datos_task = PythonOperator(task_id='manejo_tipos_datos', python_callable=process_data_manejo_tipos_datos, dag=dag)
#manejo_filas_duplicadas_task = PythonOperator(task_id='manejo_filas_duplicadas', python_callable=process_data_manejo_filas_duplicadas, dag=dag)
load_data_task = PythonOperator(task_id='load_data_to_bigquery', python_callable=load_data_to_bigquery, provide_context=True, dag=dag)

end_task = DummyOperator(task_id='end', dag=dag)

# Definición de las dependencias de las tareas
start_task >> download_task
download_task >> manejo_valores_nulos_task >> load_data_task
load_data_task >> end_task