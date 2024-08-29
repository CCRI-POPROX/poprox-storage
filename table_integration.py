import psycopg2
from sqlalchemy import create_engine
from datetime import datetime, timezone
from typing import List

# Import the Article class from poprox-concepts
from poprox_concepts.domain.article import Article

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

    return {row[2]: row for row in first_db_data}  # Return data as a dictionary keyed by URL

# Step 2: Connect to the second database using SQLAlchemy and fetch data
def fetch_second_db_data():
    engine = create_engine('postgresql://username:password@localhost:5432/second_db')
    session = engine.connect()

    article_repo = DbArticleRepository(connection=session)
    articles: List[Article] = article_repo.fetch_articles_before(days_ago=1)

    session.close()
    return articles

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
