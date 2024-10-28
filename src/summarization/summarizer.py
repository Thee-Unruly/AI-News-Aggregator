import json
import re
import torch
from transformers import BartTokenizer, BartForConditionalGeneration
from transformers import T5Tokenizer, T5ForConditionalGeneration

class BARTSummarizer:
    def __init__(self):
        model_name = 'facebook/bart-large-cnn'
        self.tokenizer = BartTokenizer.from_pretrained(model_name)
        self.model = BartForConditionalGeneration.from_pretrained(model_name)

    def summarize_bart(self, text):
        truncated_info = self.extract_truncated_info(text)
        text = self.preprocess_text(text)
        inputs = self.tokenizer(text, return_tensors='pt', max_length=1024, truncation=True)
        summary_ids = self.model.generate(inputs['input_ids'], max_length=150, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary + f" {truncated_info}" if truncated_info else summary

    @staticmethod
    def preprocess_text(text):
        # Remove unwanted annotations except for truncated characters
        return re.sub(r'\[\+?\d+\s*chars\]', '', text).strip()

    @staticmethod
    def extract_truncated_info(text):
        # Extract the truncated characters information
        match = re.search(r'\[\+(\d+)\s*chars\]', text)
        return f"[+{match.group(1)} chars]" if match else ""

class T5Summarizer:
    def __init__(self):
        model_name = 't5-base'
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)

    def summarize_t5(self, text):
        truncated_info = self.extract_truncated_info(text)
        text = self.preprocess_text(text)
        input_text = f"summarize: {text}"
        inputs = self.tokenizer(input_text, return_tensors='pt', max_length=512, truncation=True)
        summary_ids = self.model.generate(inputs['input_ids'], max_length=150, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary + f" {truncated_info}" if truncated_info else summary

    @staticmethod
    def preprocess_text(text):
        # Remove unwanted annotations except for truncated characters
        return re.sub(r'\[\+?\d+\s*chars\]', '', text).strip()

    @staticmethod
    def extract_truncated_info(text):
        # Extract the truncated characters information
        match = re.search(r'\[\+(\d+)\s*chars\]', text)
        return f"[+{match.group(1)} chars]" if match else ""

def main():
    # Load your JSON data
    try:
        with open('data/processed/processed_news_data.json') as f:
            news_data = json.load(f)
    except FileNotFoundError:
        print("Error: The specified JSON file was not found.")
        return

    # Initialize summarizers
    bart_summarizer = BARTSummarizer()
    t5_summarizer = T5Summarizer()

    for article in news_data:
        title = article.get('title', 'No Title')
        content = article.get('content', 'No Content')  # Use .get() to avoid KeyErrors
        
        print(f"Title: {title}\n")

        # Summarize with BART
        bart_summary = bart_summarizer.summarize_bart(content)
        print(f"BART Summary: {bart_summary}\n")

        # Summarize with T5
        t5_summary = t5_summarizer.summarize_t5(content)
        print(f"T5 Summary: {t5_summary}\n")

        print("=" * 80)

if __name__ == "__main__":
    main()
