import json
import os
import sys
import re

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import your API keys from the config file
from config import NEWS_API_KEY, CURRENTS_API_KEY, GNEWS_API_KEY, CNN_RSS_URL

def load_raw_data(filename):
    """Load raw data from a JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def process_news_data(raw_data, source):
    """Process raw news data into a structured format."""
    processed_data = []

    if source == 'news_api':
        articles = raw_data.get('articles', [])
    elif source == 'currents':
        articles = raw_data.get('news', [])
    elif source == 'gnews':
        articles = raw_data.get('articles', [])
    elif source == 'cnn':
        articles = raw_data  # CNN returns a list of entries
    else:
        print(f"Unknown source: {source}")
        return processed_data  # Return empty if the source is unknown

    # Process each article
    for article in articles:
        if isinstance(article, dict):  # Ensure the article is a dictionary
            content = article.get('content') or article.get('body')  # Handle different field names
            
            # No truncation; use full content directly
            content = content.strip() if content else ""

            processed_data.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'publishedAt': article.get('publishedAt') or article.get('published'),  # Handle different field names
                'source': article.get('source', {}).get('name', 'Unknown'),  # Adjust as necessary
                'url': article.get('url'),
                'content': content,  # Full content without truncation
            })
        else:
            print("Unexpected article format:", article)  # Print unexpected format

    return processed_data

def save_processed_data(filename, data):
    """Save processed data to a JSON file."""
    # Create the 'data/processed' directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Save data to JSON file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    sources = {
        'news_api': 'data/raw/news_api_raw.json',
        'currents': 'data/raw/currents_raw.json',
        'gnews': 'data/raw/gnews_raw.json',
        'cnn': 'data/raw/cnn_raw.json'
    }
    
    processed_all_data = []
    
    for source, filepath in sources.items():
        raw_data = load_raw_data(filepath)
        print(f"Processing data from {source}...")
        processed_data = process_news_data(raw_data, source)
        processed_all_data.extend(processed_data)

    # Save all processed data
    save_processed_data('data/processed/processed_news_data.json', processed_all_data)
    print("All news data processed and stored successfully.")

if __name__ == "__main__":
    main()
