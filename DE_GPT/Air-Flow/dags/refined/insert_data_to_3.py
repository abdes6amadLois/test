from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow import DAG
from datetime import datetime, timedelta
import logging
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Configurer le logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

setup_logging()

# Transformer et insérer les données dans plusieurs tables
def transform_data(**kwargs):
    try:
        hook = PostgresHook(postgres_conn_id='postgres_default')
        conn = hook.get_conn()
        cursor = conn.cursor()
        
        # Lire les données sources
        query = "SELECT * FROM raw.sales"
        cursor.execute(query)
        results = cursor.fetchall()
        logging.info(f"Nombre de lignes récupérées : {len(results)}")

        # Insérer dans les tables cibles
        for row in results:
            logging.info(f"Traitement de la ligne : {row}")

            # Insérer les données dans la table refined.customer
            cursor.execute("""
                INSERT INTO refined.customer (
                    customer_id, customer_name, age, email, country, postal_code
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING;
            """, row[0:6])

            # Insérer les données dans la table refined.product
            cursor.execute("""
                INSERT INTO refined.product (
                    product_id, product_name, quantity, price_unit
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_id) DO NOTHING;
            """, row[9:])

            # Insérer les données dans la table refined.purchase
            cursor.execute("""
                INSERT INTO refined.command (
                    purchase_id, purchase_quantity, purchase_date,
                    product_id, customer_id
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (purchase_id) DO NOTHING;
            """, row[6:10] + (row[0],))  # Ajout de customer_id

            

        conn.commit()
        logging.info("Toutes les données ont été insérées avec succès.")

    except Exception as e:
        logging.error(f"Erreur lors de l'insertion des données : {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# Configuration par défaut pour le DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=10),
    'start_date': datetime(2024, 11, 1),
}

# Définir le DAG
with DAG(
    'load_customers_data_to_db',
    default_args=default_args,
    description='Charger des données de raw.sales vers refined.*',
    schedule_interval=None,  # Exécuté uniquement sur déclenchement manuel
    catchup=False
) as dag:

    # Attendre la fin du DAG raw_api_sales_data
    wait_for_sales_raw_dag = ExternalTaskSensor(
        task_id='wait_for_dag_load_sales_data_to_db',
        external_dag_id='raw_api_sales_data',
        external_task_id='insert_sales_data',
        mode='poke',  # Utilisez 'reschedule' si le DAG doit attendre longtemps
        timeout=3600,  # Timeout après 1 heure
        poke_interval=30  # Vérifie toutes les 30 secondes
    )

    # Transformer et insérer les données
    insert_data_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data
    )

    # Définir la dépendance entre les tâches
wait_for_sales_raw_dag >> insert_data_task
