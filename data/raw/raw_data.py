import requests
import json
import os
import feedparser
import sys

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import NEWS_API_KEY, CURRENTS_API_KEY, GNEWS_API_KEY, CNN_RSS_URL

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

if __name__ == "__main__":
    # Fetch and save news from each source
    print("Fetching news from News API...")
    news_api_data = fetch_news_from_news_api()
    save_raw_data('data/raw/news_api_raw.json', news_api_data)

    print("Fetching news from Currents API...")
    currents_data = fetch_news_from_currents()
    save_raw_data('data/raw/currents_raw.json', currents_data)

    print("Fetching news from GNews API...")
    gnews_data = fetch_news_from_gnews()
    save_raw_data('data/raw/gnews_raw.json', gnews_data)

    print("Fetching news from CNN RSS Feed...")
    cnn_news_data = fetch_news_from_cnn_rss()
    save_raw_data('data/raw/cnn_raw.json', cnn_news_data)

    print("All news data fetched and stored successfully.")
