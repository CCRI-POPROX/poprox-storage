# This script scrapes articles from the AP News website and saves them to a CSV file.
# Then it connects to a PostgreSQL database and creates a table to store the articles.

import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import psycopg2


# Function to request and parse via BeautifulSoup
def request_and_parse(url):
    time.sleep(random.random())  # Add a random waiting time (less than 1 sec) for each request
    response = requests.get(url)
    return BeautifulSoup(response.content, 'html.parser')


# Helper function to extract article information
def extract_article_info(story, section, level):
    # Find the title and URL
    story_title = story.find('h3', class_="PagePromo-title")
    story_link = story_title.find('a', class_='Link', href=True)
    story_title_text = story_link.find('span', class_='PagePromoContentIcons-text').get_text()
    story_url = story_link['href']

    # Check if there is a description
    story_blurb = None
    story_description = story.find('div', class_='PagePromo-description')
    if story_description:
        story_blurb = story_description.find('span', class_='PagePromoContentIcons-text').get_text()

    # Check if there is an image
    story_image_url = None
    story_image = story.find('img', class_='Image')
    if story_image:
        story_image_url = story_image['src']

    # Add a scraped_at timestamp
    scraped_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        'title': story_title_text,
        'description': story_blurb,
        'url': story_url,
        'section': section,
        'level': level,
        'image_url': story_image_url,
        'scraped_at': scraped_at
    }


# AP News has different layouts for different sections,
# that's why we need different functions to scrape each section

# Function to scrape the Front Page
def scrape_front_page(url):
    soup = request_and_parse(url)
    articles = []

    # Locate the main section of the page, sometimes it's the first div, sometimes it's the second.
    main_section = soup.select_one('body > div.Page-content.An_Home.pageMainContent > main > div:nth-child(1)')

    # Scrape the story 1 section
    story_1_section = main_section.find_all('div', class_='PageListStandardE-items')
    for story in story_1_section:
        articles.append(extract_article_info(story, 'Front Page', 'Story 1'))

    # Scrape the story 2 section
    story_2 = main_section.find('bsp-list-loadmore', class_='PageListStandardB')
    if story_2:
        for story in story_2.find_all('div', class_='PageList-items-item'):
            articles.append(extract_article_info(story, 'Front Page', 'Story 2'))

    # Scrape the story 3 section
    story_3 = main_section.find('div', class_='PageListRightRailA')
    if story_3:
        for story in story_3.find_all('div', class_='PagePromo'):
            articles.append(extract_article_info(story, 'Front Page', 'Story 3'))

    return articles


# Function to scrape the US News or other sections with a similar structure
def scrape_others(url, section):
    soup = request_and_parse(url)
    articles = []

    # Locate the main section of the page
    main_section = soup.find('div', class_='PageListStandardH')
    stories = main_section.find_all('div', class_='PageList-items-item')

    # Scrape all the stories
    for idx, story in enumerate(stories):
        level = 'Story 1' if idx == 0 else 'Story 2'
        articles.append(extract_article_info(story, section, level))

    return articles


# Function to scrape the Science section
def scrape_science(url):
    soup = request_and_parse(url)
    articles = []

    # Locate the main section of the page, with the left and right columns
    main_section = soup.select_one('body > div.Page-content > main > div:nth-child(1)')
    left_column = soup.find('div', class_='PageListStandardH')
    right_column = soup.find('div', class_='PageListRightRailA')

    for idx, story in enumerate(left_column.find_all('div', class_='PageList-items-item')):
        level = 'Story 1' if idx == 0 else 'Story 2'
        articles.append(extract_article_info(story, 'Science', level))

    for idx, story in enumerate(right_column.find_all('div', class_='PagePromo')):
        level = 'Story 2' if idx == 0 else 'Story 3'
        articles.append(extract_article_info(story, 'Science', level))

    return articles


# URLs for different sections
urls = {
    'Front Page': 'https://apnews.com/',
    'US News': 'https://apnews.com/us-news',
    'Politics': 'https://apnews.com/politics',
    'Sports': 'https://apnews.com/sports',
    'Entertainment': 'https://apnews.com/entertainment',
    'Business': 'https://apnews.com/business',
    'Science': 'https://apnews.com/science',
    'Oddities': 'https://apnews.com/oddities'
}

articles = []

# Scrape the Front Page
print("Scraping the Front Page...")
front_page_articles = scrape_front_page('https://apnews.com/')
articles.extend(front_page_articles)

# Scrape all other sections but Science
print("Scraping other sections...")
for section, url in urls.items():
    if section != 'Front Page' and section != 'Science':
        section_articles = scrape_others(url, section)
        articles.extend(section_articles)

# Scrape the Science section
print("Scraping the Science section...")
science_articles = scrape_science('https://apnews.com/science')
articles.extend(science_articles)

# Create a DataFrame from the list of articles
print(f"Scraping finished! Total articles scraped: {len(articles)}")
print("Creating a DataFrame...")
df = pd.DataFrame(articles)
print(df.head())

# Add a time stamp to the file name
now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d_%H-%M-%S")

# Save to the folder "articles"
path_to_save = f'scraped-articles/apnews_articles_{now}.csv'
df.to_csv(path_to_save, index=False)
print(f'Articles saved to {path_to_save}')

# Database Connection and Table Creation

# Database connection parameters
conn_params = {
    "dbname": "poprox",
    "user": "postgres",
    "password": "thisisapoproxpassword",
    "host": "127.0.0.1",
    "port": "5433",
}

# Connect to the PostgreSQL server
try:
    conn = psycopg2.connect(**conn_params)
    print("Connection successful!")

    # Create a cursor object
    cur = conn.cursor()

    # Check if the 'scraped_articles' table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'scraped_articles'
        );
    """)

    table_exists = cur.fetchone()[0]

    # If the 'scraped_articles' table doesn't exist, create it
    if not table_exists:
        cur.execute("""
            CREATE TABLE scraped_articles (
                title VARCHAR,
                description VARCHAR,
                url VARCHAR PRIMARY KEY,
                section VARCHAR,
                level VARCHAR,
                image_url VARCHAR,
                scraped_at TIMESTAMP
            );
        """)
        print("Table 'scraped_articles' created successfully!")
    else:
        print("Table 'scraped_articles' already exists.")

    # Query to get the table schema
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'scraped_articles';
    """)

    # Fetch all the results
    schema = cur.fetchall()

    # Print the schema of the table
    print("Schema of the 'scraped_articles' table:")
    for column in schema:
        print(f"Column: {column[0]}, Data Type: {column[1]}")

    # Insert the data into the table
    for idx, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO scraped_articles (title, description, url, section, level, image_url, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;  -- To avoid duplicate entries based on the URL
            """, (
                row['title'],
                row['description'],
                row['url'],
                row['section'],
                row['level'],
                row['image_url'],
                row['scraped_at']
            ))
            print(f"Inserted row {idx + 1} into 'scraped_articles' table.")
        except Exception as e:
            print(f"Error inserting row {idx + 1}: {e}")

    # Check if the data was inserted correctly
    cur.execute("SELECT COUNT(*) FROM scraped_articles;")
    count = cur.fetchone()[0]
    print(f"Total rows in the 'scraped_articles' table: {count}")

    # Close the cursor and connection
    cur.close()
    conn.close()

except Exception as e:
    print(f"Error connecting to the database: {e}")
