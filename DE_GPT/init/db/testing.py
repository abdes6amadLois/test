import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",  # Remplacez par l'adresse de votre serveur
        database="airflow",  # Remplacez par le nom de votre base de données
        user="airflow",  # Remplacez par votre utilisateur
        password="airflow",  # Remplacez par votre mot de passe
        port=5432  # Assurez-vous que le port est correct
    )
    cur = conn.cursor()
    print("Connexion réussie à PostgreSQL")
    # Write your SQL query
    query = "SELECT * FROM raw.sales"
    # Execute the query
    cur.execute(query)
    results = cur.fetchall()
    for row in results:
        print(row[0,3])
        break

except Exception as e:
    print(f"Erreur de connexion à PostgreSQL: {e}")