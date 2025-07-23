import re
import json
import os
import time
from datetime import datetime
from PIL import Image, ExifTags # Import Image and ExifTags
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from file_utils import sanitize_filename  # Import sanitize_filename



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

def extract_date_from_filename(filename):
    """
    Extracts a date (YYYY-MM-DD, YYYYMMDD, YYYY_MM_DD) from a filename.
    Returns the date string if found, otherwise "null".
    """
    # Regex for YYYY-MM-DD or YYYY_MM_DD
    match = re.search(r'(\d{4}[-_\.]\d{2}[-_\.]\d{2})', filename)
    if match:
        date_str = match.group(1)
        return date_str.replace('_', '-').replace('.', '-')

    # Regex for YYYYMMDD
    match = re.search(r'(\d{8})', filename)
    if match:
        date_str = match.group(1)
        # Basic validation for YYYYMMDD to avoid matching random 8 digits
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except ValueError:
            pass
    return "null"

def generate_image_metadata(image_path, progress, task_id, image_inference, text_inference):
    """Generate description, folder name, and filename for an image file."""

    # Total steps in processing an image
    total_steps = 2 # One for vision inference, one for text inference

    # Step 1: Generate description using image_inference
    description_prompt = "Please provide a detailed description of this image, focusing on the main subject and any important details."
    description = image_inference.generate_vision(description_prompt, image_path).strip()
    progress.update(task_id, advance=1 / total_steps)

    # Step 2: Generate filename and folder name using text_inference based on the description
    exif_date = get_date_from_exif(image_path)
    filename_only = os.path.basename(image_path)
    date_from_filename = extract_date_from_filename(filename_only)

    # Determine the date to pass to the LLM, prioritizing non-null values.
    # If both are null, then try LLM extraction from description or filename.
    llm_date_for_prompt = "null"
    if exif_date:
        llm_date_for_prompt = exif_date
    elif date_from_filename != "null":
        llm_date_for_prompt = date_from_filename
    else:
        # Ask LLM to extract date from filename if not found elsewhere
        date_extraction_prompt = f"""Extract a date in YYYY-MM-DD format from the following text. If no date is found, output 'null'.
Text: {filename_only}
Date:"""
        llm_extracted_date = text_inference.generate(date_extraction_prompt).strip()
        if re.match(r'\d{4}-\d{2}-\d{2}', llm_extracted_date):
            llm_date_for_prompt = llm_extracted_date
        else:
            # If still no date, try from description (existing logic, but now part of this flow)
            date_extraction_prompt = f"""Extract a date in YYYY-MM-DD format from the following text. If no date is found, output 'null'.
Text: {description}
Date:"""
            llm_extracted_date = text_inference.generate(date_extraction_prompt).strip()
            if re.match(r'\d{4}-\d{2}-\d{2}', llm_extracted_date):
                llm_date_for_prompt = llm_extracted_date
            else:
                llm_date_for_prompt = "null"

    prompt = f"""Based on the description below, the EXIF date (if any), and the date extracted from the filename (if any), generate a suitable folder name (max 2 words, nouns only) and a descriptive filename (max 3 words, nouns only, underscores for spaces). Consider incorporating the most relevant date into the filename if appropriate.

Description: {description}
Date for consideration: {llm_date_for_prompt}

Example:
Description: A photo of a sunset over the mountains.
EXIF Date: null
Date from Filename: null
JSON Output: {{ "foldername": "landscapes", "filename": "sunset_over_mountains" }}

Example:
Description: A photo of a birthday party.
EXIF Date: 2023-01-15
Date from Filename: null
JSON Output: {{ "foldername": "events", "filename": "2023-01-15 birthday_party" }}

Example:
Description: A photo of a document scanned.
EXIF Date: null
Date from Filename: 2024-03-10
JSON Output: {{ "foldername": "documents", "filename": "2024-03-10 scanned_document" }}

Generate ONLY the JSON output, nothing else. Do not include any conversational text.

JSON Output:"""
    output = text_inference.generate(prompt).strip()
    # Use regex to find a JSON object within the output
    json_match = re.search(r'\{.*?\}', output, re.DOTALL)
    if not json_match:
        raise ValueError(f"Could not find JSON in model output: {output}")

    json_string = json_match.group(0)

    try:
        response_json = json.loads(json_string)
        foldername = sanitize_filename(response_json.get("foldername", ""))
        filename = sanitize_filename(response_json.get("filename", ""))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from model output: {json_string}. Error: {e}")

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

def get_date_from_exif(image_path):
    """
    Extracts the date from an image's EXIF data.
    Returns date in 'YYYY-MM-DD' format if found, otherwise None.
    """
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                if tag_name == 'DateTimeOriginal':
                    # EXIF date format is 'YYYY:MM:DD HH:MM:SS'
                    dt_object = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                    return dt_object.strftime('%Y-%m-%d')
                elif tag_name == 'DateTime':
                    dt_object = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                    return dt_object.strftime('%Y-%m-%d')
    except Exception:
        # print(f"Error reading EXIF data from {image_path}")
        pass
    return None
