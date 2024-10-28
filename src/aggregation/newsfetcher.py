#fetch news from the various APIs

import requests
import feedparser
import sys
import os

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

if __name__ == "__main__":
    # Example usage
    print("Fetching news from News API...")
    news_api_data = fetch_news_from_news_api()
    print(news_api_data)

    print("Fetching news from Currents API...")
    currents_data = fetch_news_from_currents()
    print(currents_data)

    print("Fetching news from GNews API...")
    gnews_data = fetch_news_from_gnews()
    print(gnews_data)

    print("Fetching news from CNN RSS Feed...")
    cnn_news_data = fetch_news_from_cnn_rss()
    print(cnn_news_data)