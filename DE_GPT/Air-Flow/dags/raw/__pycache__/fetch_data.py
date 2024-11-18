# Code corrigé pour éviter les problèmes potentiels
from airflow.operators.python import PythonOperator
from airflow import DAG
from datetime import datetime, timedelta
import pandas as pd
import logging
from io import StringIO
import requests
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Helpers
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

setup_logging()

# Fetch API Sales Data
def fetch_api_sales_data(**kwargs):
    api_url = "https://my.api.mockaroo.com/sales"
    headers = {"X-API-Key": "0f6d42d0"}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = pd.read_csv(StringIO(response.text))
        data_dict = data.to_dict(orient="records")
        logging.info("Successfully fetched sales data from the API.")
        kwargs['ti'].xcom_push(key='sales_data', value=data_dict)
    except Exception as e:
        logging.error(f"Failed to fetch data from API: {e}")
        raise

# Insert Data into PostgreSQL
def insert_sales_data(**kwargs):
    sales_data = kwargs['ti'].xcom_pull(task_ids="fetch_api_sales_data", key="sales_data")
    if not sales_data:
        logging.error("No sales data found in XCom.")
        return
    
    hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO raw.sales (
            customer_id, customer_name, age, email, country, postal_code,
            purchase_id, purchase_quantity, purchase_date,
            product_id, product_name, quantity, price_unit
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        for row in sales_data:
            cursor.execute(insert_query, (
                row["customer_id"], row["customer_name"], row["age"], row["email"],
                row["country"], row["postal_code"], row["purchase_id"],
                row["purchase_quantity"], row["purchase_date"], row["product_id"],
                row["product_name"], row["quantity"], row["price_unit"]
            ))
        conn.commit()
        logging.info("Sales data successfully inserted into PostgreSQL.")
    except Exception as e:
        logging.error(f"Failed to insert data into PostgreSQL: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# DAG Definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=5),
    'start_date': datetime(2024, 11, 1),
}

with DAG(
    'raw_api_sales_data',
    default_args=default_args,
    description='load sales data from sales API to PostgreSQL',
    schedule_interval='*/10 * * * *',
    catchup=False
) as dag:
    fetch_data_task = PythonOperator(
        task_id="fetch_api_sales_data",
        python_callable=fetch_api_sales_data,
    )
    insert_data_task = PythonOperator(
        task_id="insert_sales_data",
        python_callable=insert_sales_data,
    )
    fetch_data_task >> insert_data_task
