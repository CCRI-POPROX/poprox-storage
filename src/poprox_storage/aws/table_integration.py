import psycopg2
from sqlalchemy import create_engine
from typing import List
from poprox_concepts.domain.article import Article
from src.poprox_storage.repositories.data_stores.db import DbArticleRepository
from s3 import S3
import boto3

# Step 1: Connect to the first PostgreSQL database and fetch data
def fetch_first_db_data():
    conn_params = {
        "dbname": "poprox",
        "user": "postgres",
        "password": "thisisapoproxpassword",
        "host": "127.0.0.1",
        "port": "5433",
    }

    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    cur.execute("SELECT title, description, url, section, level, image_url, scraped_at FROM test_scraped_articles;")
    first_db_data = cur.fetchall()

    cur.close()
    conn.close()

    return {row[2]: row for row in first_db_data}  

# Step 2: Connect to the second database using SQLAlchemy and fetch data
def fetch_s3_data(bucket_name: str, key: str):
    session = boto3.Session()
    s3 = S3(session)

    s3_object = s3.get_object(bucket_name, key)
    data = json.loads(s3_object['Body'].read().decode('utf-8'))
    
    return [Article(**item) for item in data]

# Step 3: Combine data from both sources based on the URL
def combine_data(first_db_data, second_db_data):
    combined_data = []
    for article in second_db_data:
        url = article.url
        if url in first_db_data:
            combined_record = Article(
                title=first_db_data[url][0],
                content=None,  
                url=url,
                preview_image_id=None,  
                published_at=article.published_at,
                mentions=[], 
                source=article.source,
                external_id=None, 
                raw_data=None,  
                popularity=article.popularity  
            )
            combined_data.append(combined_record.dict())
    return combined_data

if __name__ == "__main__":
    first_db_data = fetch_first_db_data()
    second_db_data = fetch_second_db_data()
    combined_data = combine_data(first_db_data, second_db_data)
    
    # Save combined data to a file or pass it to poprox-platform for S3 upload
    with open('combined_data.json', 'w') as f:
        import json
        json.dump(combined_data, f, default=str)

    print("Data merging complete. Combined data saved to 'combined_data.json'.")
