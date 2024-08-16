# This test checks if a new table for scraped articles can be created in the PostgreSQL database
# To test: run `pytest test_create_scrape_table.py` in the poprox-db/tests directory

import psycopg2
from sqlalchemy import create_engine
import pandas as pd

# Database connection parameters
conn_params = {
    "dbname": "poprox",
    "user": "postgres",
    "password": "thisisapoproxpassword",
    "host": "127.0.0.1",
    "port": "5433",
}

# Create a SQLAlchemy engine
engine = create_engine(
    f'postgresql+psycopg2://{conn_params["user"]}:{conn_params["password"]}@{conn_params["host"]}:{conn_params["port"]}/{conn_params["dbname"]}')


# Function to test the creation of a new table and insertion of data
def test_create_scrape_table():
    # Connect to the PostgreSQL server
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    # Create a new table for testing
    cur.execute("""
        CREATE TABLE test_scraped_articles (
            title VARCHAR,
            description VARCHAR,
            url VARCHAR PRIMARY KEY,
            section VARCHAR,
            level VARCHAR,
            image_url VARCHAR,
            scraped_at TIMESTAMP
        );
    """)
    conn.commit()

    # Check if the table was created successfully
    cur.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'test_scraped_articles'
        );
    """)
    table_exists = cur.fetchone()[0]

    assert table_exists, "Table 'test_scraped_articles' was not created successfully!"

    # Clean up
    cur.execute("DROP TABLE test_scraped_articles;")
    conn.commit()

    cur.close()
    conn.close()

    print("Table creation test passed successfully!")
