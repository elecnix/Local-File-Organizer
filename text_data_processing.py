import re
import json
import os
import time
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from data_processing_common import sanitize_filename

def summarize_text_content(text, text_inference):
    """Summarize the given text content."""
    prompt = f"""Provide a concise and accurate summary of the following text, focusing on the main ideas and key details.
Limit your summary to a maximum of 150 words.

Text: {text}

Summary:"""

    summary = text_inference.generate(prompt).strip()
    return summary

def process_single_text_file(args, text_inference, silent=False, log_file=None):
    """Process a single text file to generate metadata."""
    file_path, text = args
    start_time = time.time()

    # Create a Progress instance for this file
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    ) as progress:
        task_id = progress.add_task(f"Processing {os.path.basename(file_path)}", total=1.0)
        foldername, filename, description = generate_text_metadata(text, file_path, progress, task_id, text_inference)

    end_time = time.time()
    time_taken = end_time - start_time

    message = f"File: {file_path}\nTime taken: {time_taken:.2f} seconds\nDescription: {description}\nFolder name: {foldername}\nGenerated filename: {filename}\n"
    if silent:
        if log_file:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
    else:
        print(message)
    return {
        'file_path': file_path,
        'foldername': foldername,
        'filename': filename,
        'description': description
    }

def process_text_files(text_tuples, text_inference, silent=False, log_file=None):
    """Process text files sequentially."""
    results = []
    for args in text_tuples:
        data = process_single_text_file(args, text_inference, silent=silent, log_file=log_file)
        results.append(data)
    return results

def generate_text_metadata(input_text, file_path, progress, task_id, text_inference):
    """Generate description, folder name, and filename for a text document."""

    # Total steps in processing a text file
    total_steps = 1

    # Step 1: Generate description, folder name, and filename in one go
    prompt = f"""Analyze the following text and provide a concise description, a suitable folder name (max 2 words, nouns only), and a descriptive filename (max 3 words, nouns only, underscores for spaces). Return the output as a JSON object with keys 'description', 'foldername', and 'filename'.

Example:
Text: This document discusses the principles of quantum mechanics and its applications.
JSON Output: {{ "description": "Principles and applications of quantum mechanics", "foldername": "physics", "filename": "quantum_mechanics_principles" }}

Text: {input_text}

JSON Output:"""
    output = text_inference.generate(prompt).strip()
    # Extract JSON string using regex
    json_match = re.search(r'\{.*\}', output, re.DOTALL)
    if json_match:
        json_string = json_match.group(0)
        output_dict = json.loads(json_string)
    else:
        raise ValueError(f"Could not find JSON in model output: {output}")
    description = output_dict['description']
    foldername = output_dict['foldername']
    filename = output_dict['filename']

    progress.update(task_id, advance=1 / total_steps)

    # Remove unwanted words and stopwords
    unwanted_words = set([
        'the', 'and', 'based', 'generated', 'this', 'is', 'filename', 'file', 'document', 'text', 'output', 'only', 'below', 'category',
        'summary', 'key', 'details', 'information', 'note', 'notes', 'main', 'ideas', 'concepts', 'in', 'on', 'of', 'with', 'by', 'for',
        'to', 'from', 'a', 'an', 'as', 'at', 'i', 'we', 'you', 'they', 'he', 'she', 'it', 'that', 'which', 'are', 'were', 'was', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'but', 'if', 'or', 'because', 'about', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'any', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'new', 'depicts', 'show', 'shows', 'display',
        'illustrates', 'presents', 'features', 'provides', 'covers', 'includes', 'discusses', 'demonstrates', 'describes'
    ])
    stop_words = set(stopwords.words('english'))
    all_unwanted_words = unwanted_words.union(stop_words)
    lemmatizer = WordNetLemmatizer()

    # Function to clean and process the AI output
    def clean_ai_output(text, max_words):
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        text = text.strip()
        # Split concatenated words (e.g., 'mathOperations' -> 'math Operations')
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        # Tokenize and lemmatize words
        words = word_tokenize(text)
        words = [word.lower() for word in words if word.isalpha()]
        words = [lemmatizer.lemmatize(word) for word in words]
        # Remove unwanted words and duplicates
        filtered_words = []
        seen = set()
        for word in words:
            if word not in all_unwanted_words and word not in seen:
                filtered_words.append(word)
                seen.add(word)
        # Limit to max words
        filtered_words = filtered_words[:max_words]
        return '_'.join(filtered_words)

    # Process filename
    filename = clean_ai_output(filename, max_words=3)
    if not filename or filename.lower() in ('untitled', ''):
        # Use keywords from the description
        filename = clean_ai_output(description, max_words=3)
    if not filename:
        filename = 'document_' + os.path.splitext(os.path.basename(file_path))[0]

    sanitized_filename = sanitize_filename(filename, max_words=3)

    # Process foldername
    foldername = clean_ai_output(foldername, max_words=2)
    if not foldername or foldername.lower() in ('untitled', ''):
        # Attempt to extract keywords from the description
        foldername = clean_ai_output(description, max_words=2)
        if not foldername:
            foldername = 'documents'

    sanitized_foldername = sanitize_filename(foldername, max_words=2)

    return sanitized_foldername, sanitized_filename, description
