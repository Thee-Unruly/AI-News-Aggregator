import json
import re
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
import torch
from datasets import Dataset
from transformers import logging as transformers_logging

# Optional: Set verbosity level to reduce warnings
transformers_logging.set_verbosity_error()

# Load JSON data
try:
    with open('data/processed/processed_news_data.json') as f:
        news_data = json.load(f)
except FileNotFoundError:
    print("Error: The specified JSON file was not found.")
    news_data = []

# Preprocess the content data and create labels
def preprocess_text(text):
    return re.sub(r'\[\+?\d+\s*chars\]', '', text).strip().lower()

documents = [preprocess_text(article['content']) for article in news_data if 'content' in article]
labels = [1 if "good" in doc else 0 for doc in documents]

# DataFrame and split
df = pd.DataFrame({'text': documents, 'label': labels})
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['text'], df['label'], test_size=0.2, random_state=42
)

# Load model and tokenizer
model_name = "bert-base-uncased"
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Tokenize the training and validation texts
train_encodings = tokenizer(list(train_texts), truncation=True, padding=True)
val_encodings = tokenizer(list(val_texts), truncation=True, padding=True)

# Convert labels to lists
train_labels = train_labels.tolist()
val_labels = val_labels.tolist()

# Create Dataset objects
train_dataset = Dataset.from_dict({
    'input_ids': train_encodings['input_ids'], 
    'attention_mask': train_encodings['attention_mask'],
    'label': torch.tensor(train_labels, dtype=torch.long)
})

val_dataset = Dataset.from_dict({
    'input_ids': val_encodings['input_ids'], 
    'attention_mask': val_encodings['attention_mask'],
    'label': torch.tensor(val_labels, dtype=torch.long)
})

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=10,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    load_best_model_at_end=True,
    evaluation_strategy="epoch",
    save_strategy="epoch",
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset
)

# Train and evaluate
train_results = trainer.train()
eval_results = trainer.evaluate()

# Save the model and tokenizer
model.save_pretrained('./fine-tuned-model')
tokenizer.save_pretrained('./fine-tuned-model')

# Extract losses for plotting
train_loss = []
eval_loss = []

# Extract training losses from logs
for log in trainer.state.log_history:
    if 'loss' in log:
        train_loss.append(log['loss'])
    if 'eval_loss' in log:
        eval_loss.append(log['eval_loss'])

# Prepare for plotting
epochs = range(1, len(train_loss) + 1)

plt.plot(epochs, train_loss, label='Training Loss')
plt.plot(range(1, len(eval_loss) + 1), eval_loss, label='Validation Loss')  # Adjust x-axis for eval loss
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Training and Validation Loss Over Epochs')
plt.legend()
plt.show()

# Function to check model predictions
def analyze_predictions(model, texts):
    inputs = tokenizer(texts, return_tensors='pt', truncation=True, padding=True)
    outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=1)
    return predictions

# Test the model on new data
test_texts = ["This is a good day.", "The stock market is crashing!"]
predictions = analyze_predictions(model, test_texts)
print(predictions.tolist())  # Outputs the predicted labels
