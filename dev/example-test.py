import psycopg2

# Define your connection parameters for the initial connection
conn_params = {
    "dbname": "poprox",
    "user": "postgres",
    "password": "thisisapoproxpassword",
    "host": "127.0.0.1",
    "port": "5433"
}

# Connect to the PostgreSQL server
try:
    conn = psycopg2.connect(**conn_params)
    print("Connection successful!")
    
    # Create a cursor object
    cur = conn.cursor()
    
    # Query to get the table schema
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'articles';
    """)
    
    # Fetch all the results
    schema = cur.fetchall()
    
    # Print the schema of the table
    print("Schema of the 'articles' table:")
    for column in schema:
        print(f"Column: {column[0]}, Data Type: {column[1]}")
    
    # Query to get an example row of data
    cur.execute("SELECT * FROM articles LIMIT 1;")
    
    # Fetch the example row
    example_row = cur.fetchone()
    
    # Print the example row of data
    print("\nExample row from the 'articles' table:")
    print(example_row)
    
    # Close the cursor and connection
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to the database: {e}")