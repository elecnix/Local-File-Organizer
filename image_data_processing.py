import re
import json
import os
import time
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from data_processing_common import sanitize_filename  # Import sanitize_filename



def process_single_image(image_path, image_inference, text_inference, silent=False, log_file=None):
    """Process a single image file to generate metadata."""
    start_time = time.time()

    # Create a Progress instance for this file
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    ) as progress:
        task_id = progress.add_task(f"Processing {os.path.basename(image_path)}", total=1.0)
        foldername, filename, description = generate_image_metadata(image_path, progress, task_id, image_inference, text_inference)
    
    end_time = time.time()
    time_taken = end_time - start_time

    message = f"File: {image_path}\nTime taken: {time_taken:.2f} seconds\nDescription: {description}\nFolder name: {foldername}\nGenerated filename: {filename}\n"
    if silent:
        if log_file:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
    else:
        print(message)
    return {
        'file_path': image_path,
        'foldername': foldername,
        'filename': filename,
        'description': description
    }

def process_image_files(image_paths, image_inference, text_inference, silent=False, log_file=None):
    """Process image files sequentially."""
    data_list = []
    for image_path in image_paths:
        data = process_single_image(image_path, image_inference, text_inference, silent=silent, log_file=log_file)
        data_list.append(data)
    return data_list

def generate_image_metadata(image_path, progress, task_id, image_inference, text_inference):
    """Generate description, folder name, and filename for an image file."""

    # Total steps in processing an image
    total_steps = 2 # One for vision inference, one for text inference

    # Step 1: Generate description using image_inference
    description_prompt = "Please provide a detailed description of this image, focusing on the main subject and any important details."
    description = image_inference.generate_vision(description_prompt, image_path).strip()
    progress.update(task_id, advance=1 / total_steps)

    # Step 2: Generate filename and folder name using text_inference based on the description
    prompt = f"""Based on the description below, generate a suitable folder name (max 2 words, nouns only) and a descriptive filename (max 3 words, nouns only, underscores for spaces). Return the output as a JSON object with keys 'foldername' and 'filename'.

Description: {description}

Example:
Description: A photo of a sunset over the mountains.
JSON Output: {{ "foldername": "landscapes", "filename": "sunset_over_mountains" }}

Now generate the folder name and filename.

JSON Output:"""
    output = text_inference.generate(prompt).strip()
    # Extract JSON string using regex
    json_match = re.search(r'\{.*\}', output, re.DOTALL)
    if json_match:
        json_string = json_match.group(0)
        output_dict = json.loads(json_string)
    else:
        raise ValueError(f"Could not find JSON in model output: {output}")
    foldername = output_dict['foldername']
    filename = output_dict['filename']
    progress.update(task_id, advance=1 / total_steps)

    # Remove any unwanted words and stopwords
    unwanted_words = set([
        'the', 'and', 'based', 'generated', 'this', 'is', 'filename', 'file', 'image', 'picture', 'photo',
        'folder', 'category', 'output', 'only', 'below', 'text', 'jpg', 'png', 'jpeg', 'gif', 'bmp', 'svg',
        'logo', 'in', 'on', 'of', 'with', 'by', 'for', 'to', 'from', 'a', 'an', 'as', 'at', 'red', 'blue',
        'green', 'color', 'colors', 'colored', 'text', 'graphic', 'graphics', 'main', 'subject', 'important',
        'details', 'description', 'depicts', 'show', 'shows', 'display', 'illustrates', 'presents', 'features',
        'provides', 'covers', 'includes', 'demonstrates', 'describes'
    ])
    stop_words = set(stopwords.words('english'))
    all_unwanted_words = unwanted_words.union(stop_words)
    lemmatizer = WordNetLemmatizer()

    # Function to clean and process the AI output
    def clean_ai_output(text, max_words):
        # Remove file extensions and special characters
        text = re.sub(r'\.\w{1,4}$', '', text)  # Remove file extensions like .jpg, .png
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove special characters
        text = re.sub(r'\d+', '', text)  # Remove digits
        text = text.strip()
        # Split concatenated words (e.g., 'GoogleChrome' -> 'Google Chrome')
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
        filename = 'image_' + os.path.splitext(os.path.basename(image_path))[0]

    sanitized_filename = sanitize_filename(filename, max_words=3)

    # Process foldername
    foldername = clean_ai_output(foldername, max_words=2)
    if not foldername or foldername.lower() in ('untitled', ''):
        # Attempt to extract keywords from the description
        foldername = clean_ai_output(description, max_words=2)
        if not foldername:
            foldername = 'images'

    sanitized_foldername = sanitize_filename(foldername, max_words=2)

    return sanitized_foldername, sanitized_filename, description
