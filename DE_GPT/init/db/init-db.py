import psycopg

# Connexion à PostgreSQL et création des schémas et tables
with psycopg.connect("dbname=airflow user=airflow password=airflow host=localhost port=5432") as conn:
    # Activez le mode autocommit pour exécuter chaque commande immédiatement
    conn.autocommit = True

    # Création des schémas
    schemas = ["raw", "refined", "report"]

    # Création des tables dans le schéma raw
    with conn.cursor() as cursor:
        for schema in schemas:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.sales (
                customer_id INTEGER,
                customer_name TEXT,
                age INTEGER,
                email TEXT,
                country TEXT,
                postal_code TEXT,
                purchase_id INTEGER,
                purchase_quantity INTEGER,
                purchase_date DATE,
                product_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                price_unit NUMERIC
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refined.customer (
                customer_id INT PRIMARY KEY,
                customer_name VARCHAR(25),
                age INT,
                email VARCHAR(25),
                country VARCHAR(15),
                postal_code VARCHAR(10)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refined.product (
                product_id INT PRIMARY KEY,
                product_name VARCHAR(30),
                quantity INT,
                price_unit DECIMAL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refined.command (
                purchase_id INT PRIMARY KEY,
                purchase_quantity INT,
                purchase_date DATE,
                product_id INT REFERENCES refined.product(product_id),
                customer_id INT REFERENCES refined.customer(customer_id)
            );
        """)
        

        print("Schemas and tables initialized successfully!")
