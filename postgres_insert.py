import psycopg2
from psycopg2 import errors

# Connect to the PostgreSQL server
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    user="admin",
    password="admin"
)

# Create a cursor object
cur = conn.cursor()
# set autocommit for cursor
conn.autocommit = True

# Check if the database already exists
cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'agriiq';")
database_exists = cur.fetchone()

if not database_exists:
    # Create the database
    cur.execute("CREATE DATABASE agriiq;")

# Close the cursor and connection to the default database
cur.close()
conn.close()

# Connect to the new database
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="agriiq",
    user="admin",
    password="admin"
)

# Create a cursor object for the new database
cur = conn.cursor()

# Create the table with appropriate column data types
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agmarket_monthly (
            state_name TEXT,
            district_name TEXT,
            market_name TEXT,
            variety TEXT,
            groups TEXT,
            arrivals FLOAT,
            min_price FLOAT,
            max_price FLOAT,
            model_price FLOAT,
            reported_date DATE,
            commodity TEXT
        );
    """)
    # Commit the changes
    conn.commit()
except Exception as e:
    # Rollback the transaction and handle the exception
    conn.rollback()
    print(f"Error occurred during table creation: {str(e)}")

# Insert CSV data into the table (assuming you have 'data.csv' file)
import csv

try:
    with open('agg_data.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row

        for row in reader:
            cur.execute("INSERT INTO agmarket_monthly (state_name, district_name, market_name, variety, groups, arrivals, min_price, max_price, model_price, reported_date, commodity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", row)

    # Commit the changes
    conn.commit()
except Exception as e:
    # Rollback the transaction and handle the exception
    conn.rollback()
    print(f"Error occurred during data insertion: {str(e)}")

# Close the cursor and connection
cur.close()
conn.close()
