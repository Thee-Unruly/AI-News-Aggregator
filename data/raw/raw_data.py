import requests
import json
import os
import feedparser
import sys

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import NEWS_API_KEY, CURRENTS_API_KEY, GNEWS_API_KEY, CNN_RSS_URL

# List to store URLs of news articles
article_urls = []

def fetch_news_from_news_api():
    url = f'https://newsapi.org/v2/top-headlines?apiKey={NEWS_API_KEY}&country=us'
    response = requests.get(url)
    return response.json()

def fetch_news_from_currents():
    url = f'https://api.currentsapi.services/v1/latest-news?apiKey={CURRENTS_API_KEY}'
    response = requests.get(url)
    return response.json()

def fetch_news_from_gnews():
    url = f'https://gnews.io/api/v4/top-headlines?token={GNEWS_API_KEY}&lang=en'
    response = requests.get(url)
    return response.json()

def fetch_news_from_cnn_rss():
    news_feed = feedparser.parse(CNN_RSS_URL)
    return news_feed.entries

def save_raw_data(filename, data):
    # Create the 'data/raw' directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Save data to JSON file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def save_urls(filename, urls):
    # Create the 'data/urls' directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Save URLs to JSON file
    with open(filename, 'w') as f:
        json.dump(urls, f, indent=4)

def load_existing_urls(filename):
    """Load existing URLs from the JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def extract_urls(news_data):
    # Extract URLs from news articles and add them to the article_urls list
    if 'articles' in news_data:
        for article in news_data['articles']:
            if 'url' in article:
                article_urls.append(article['url'])

if __name__ == "__main__":
    # Load existing URLs
    article_urls = load_existing_urls('data/urls/article_urls.json')

    # Fetch and save news from each source
    print("Fetching news from News API...")
    news_api_data = fetch_news_from_news_api()
    extract_urls(news_api_data)  # Extract URLs from News API
    save_raw_data('data/raw/news_api_raw.json', news_api_data)

    print("Fetching news from Currents API...")
    currents_data = fetch_news_from_currents()
    extract_urls(currents_data)  # Extract URLs from Currents API
    save_raw_data('data/raw/currents_raw.json', currents_data)

    print("Fetching news from GNews API...")
    gnews_data = fetch_news_from_gnews()
    extract_urls(gnews_data)  # Extract URLs from GNews API
    save_raw_data('data/raw/gnews_raw.json', gnews_data)

    print("Fetching news from CNN RSS Feed...")
    cnn_news_data = fetch_news_from_cnn_rss()
    # CNN RSS feeds don't follow the same structure, so we handle it separately
    for entry in cnn_news_data:
        if 'link' in entry:
            article_urls.append(entry.link)

    save_raw_data('data/raw/cnn_raw.json', cnn_news_data)

    # Save the updated URLs to a JSON file
    save_urls('data/urls/article_urls.json', article_urls)

    print("All news data fetched and stored successfully.")
    print("Article URLs have been saved successfully.")
