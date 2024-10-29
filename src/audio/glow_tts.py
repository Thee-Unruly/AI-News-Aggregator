import json
import os
import sys
import requests
import time
import re
import pyttsx3  # Import the TTS library

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import your API keys from the config file
from config import NEWS_API_KEY, CURRENTS_API_KEY, GNEWS_API_KEY, CNN_RSS_URL

def load_raw_data(filename):
    """Load raw data from a JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def extract_truncated_info(content):
    """Extract truncated characters information from the content."""
    match = re.search(r'\[\+(\d+)\s*chars\]', content)
    return f" [+{match.group(1)} chars]" if match else ""

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
        if isinstance(article, dict):
            content = article.get('content') or article.get('body')
            if content:
                truncated_info = extract_truncated_info(content)
                content = (content.split('…')[0] + truncated_info) if truncated_info else content.split('…')[0]

            # Prepare the processed data
            processed_data.append({
                'title': article.get('title', 'No Title Provided'),
                'description': article.get('description', 'No Description Provided'),
                'publishedAt': article.get('publishedAt') or article.get('published'),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'url': article.get('url'),
                'content': content.strip() if content else "",  # Strip whitespace
            })

        else:
            print("Unexpected article format:", article)

    return processed_data

def save_processed_data(filename, data):
    """Save processed data to a JSON file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    # Initialize the TTS engine
    engine = pyttsx3.init()

    # Set properties before adding anything to speak
    engine.setProperty('rate', 150)    # Speed of speech
    engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

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

    # Give the user the option to choose a title
    print("\nAvailable articles:")
    for idx, article in enumerate(processed_all_data):
        print(f"{idx + 1}: {article['title']}")  # Display titles with index

    try:
        choice = int(input("Enter the number of the article you want to hear: ")) - 1
        if 0 <= choice < len(processed_all_data):
            content_to_speak = processed_all_data[choice]['content']
            # Speak the chosen article's content
            engine.say(content_to_speak.strip() if content_to_speak else "No content available.")
            engine.runAndWait()  # Wait for the speaking to finish
        else:
            print("Invalid choice. Please select a valid article number.")
    except ValueError:
        print("Please enter a valid number.")

if __name__ == "__main__":
    main()