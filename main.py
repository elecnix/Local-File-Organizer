import os
import time
import argparse
import sys
from modes import Mode
from rich.console import Console

from file_utils import (
    display_directory_tree,
    collect_file_paths,
    separate_files_by_type,
    read_file_data
)

from data_processing_common import (
    compute_operations,
    execute_operations,
    process_files_by_date,
    process_files_by_type,
)

from text_data_processing import (
    process_text_files
)

from image_data_processing import (
    process_image_files
)

from audio_data_processing import (
    initialize_whisper_model,
    process_audio_files
)



from ollama_inference import OllamaTextInference, OllamaVLMInference # Import OllamaTextInference and OllamaVLMInference

def ensure_nltk_data():
    """Ensure that NLTK data is downloaded efficiently and quietly."""
    import nltk
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)

# Initialize models

image_inference = None
text_inference = None
audio_inference = None

def initialize_models(silent_mode=False):
    """Initialize the models if they haven't been initialized yet."""
    global image_inference, text_inference, audio_inference
    
    # Initialize Ollama for text inference
    if text_inference is None:
        model_name_text_ollama = "llama3"
        text_inference = OllamaTextInference(
            model_name=model_name_text_ollama
        )
    # Initialize Ollama for image inference
    if image_inference is None:
        model_name_image_ollama = "llava"
        image_inference = OllamaVLMInference(
            model_name=model_name_image_ollama
        )
    # Initialize Ollama for audio inference
    if audio_inference is None:
        model_name_audio_ollama = "llama3"
        audio_inference = OllamaTextInference(
            model_name=model_name_audio_ollama
        )
        if not silent_mode:
            console.print("**----------------------------------------------**")
            console.print("**       Ollama inference model initialized     **")
            console.print("**----------------------------------------------**")
    
    # Initialize Whisper model for audio transcription
    initialize_whisper_model(silent=silent_mode)

def simulate_directory_tree(operations, base_path):
    """Simulate the directory tree based on the proposed operations."""
    tree = {}
    for op in operations:
        rel_path = os.path.relpath(op['destination'], base_path)
        parts = rel_path.split(os.sep)
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    return tree

def print_simulated_tree(tree, prefix=''):
    """Print the simulated directory tree."""
    pointers = ['├── '] * (len(tree) - 1) + ['└── '] if tree else []
    for pointer, key in zip(pointers, tree):
        print(prefix + pointer + key)
        if tree[key]:  # If there are subdirectories or files
            extension = '│   ' if pointer == '├── ' else '    '
            print_simulated_tree(tree[key], prefix + extension)



console = Console()

def main():
    parser = argparse.ArgumentParser(description="Organize files based on content, date, or type.")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input_dir", type=str, help="Path of the directory to organize.")
    input_group.add_argument("--input_file", type=str, help="Path of the file to organize.")
    parser.add_argument("--output_dir", type=str, default="", help="Path to store organized files and folders (default: 'organized_folder' in input directory).")
    parser.add_argument("--mode", type=lambda m: Mode.from_int(int(m)), choices=list(Mode), required=True, help="Mode to organize files. Use 1 for By Content, 2 for By Date, or 3 for By Type.")
    parser.add_argument("--silent", type=str, choices=["yes", "no"], default="no", help="Enable silent mode (yes/no).")
    parser.add_argument("--dry_run", type=str, choices=["yes", "no"], default="yes", help="Perform a dry run without making actual changes (yes/no). Default is 'yes'.")

    args = parser.parse_args()

    silent_mode = args.silent == 'yes'

    log_file = None
    if silent_mode:
        log_file_path = os.path.join(os.getcwd(), "log.txt")
        log_file = open(log_file_path, "w")
        sys.stdout = log_file
        sys.stderr = log_file

    if args.input_dir:
        input_path = os.path.abspath(args.input_dir)
        console.print(f"Input path successfully uploaded: {input_path}")
    elif args.input_file:
        input_path = os.path.abspath(args.input_file)
        console.print(f"Input path successfully uploaded: {input_path}")
    else:
        # This case should ideally be caught by argparse, but as a fallback
        console.print("[bold red]Error: No input directory or file specified.[/bold red]")
        return

    console.print("--------------------------------------------------")

    if args.output_dir:
        output_dir = args.output_dir
    elif args.input_dir:
        output_dir = os.path.join(input_path, "organized_folder")
    elif args.input_file:
        # If a single file is processed, output to a generic 'organized_folder' in the current directory
        output_dir = os.path.join(os.getcwd(), "organized_folder")
    else:
        # Fallback for output_dir if no input is specified (shouldn't happen)
        output_dir = os.path.join(os.getcwd(), "organized_folder")
    console.print(f"Output path successfully set to: {output_dir}")
    console.print("--------------------------------------------------")

    # Ensure NLTK data is downloaded efficiently and quietly
    ensure_nltk_data()

    # Start with dry run set to True
    dry_run = args.dry_run == 'yes'

    start_time = time.time()
    file_paths = collect_file_paths(input_path)
    end_time = time.time()

    console.print(f"Time taken to load file paths: {end_time - start_time:.2f} seconds")
    console.print("--------------------------------------------------")
    console.print("Directory tree before organizing:")
    display_directory_tree(input_path)

    console.print("**************************************************")

    mode = args.mode
    operations = []

    if mode == Mode.CONTENT:
        # Proceed with content mode
        if not silent_mode:
            console.print("Checking if the model is already downloaded. If not, downloading it now.")
        initialize_models()

        if not silent_mode:
            console.print("**************************************************")
            console.print("The file upload was successful. Processing may take a few minutes.")
            console.print("**************************************************")

        # Separate files by type
        image_files, text_files, audio_files = separate_files_by_type(file_paths)

        # Prepare text tuples for processing
        text_tuples = []
        for fp in text_files:
            # Use read_file_data to read the file content
            text_content = read_file_data(fp)
            if text_content is None:
                message = f"Unsupported or unreadable text file format: {fp}"
                if silent_mode:
                    if log_file:
                        log_file.write(message + '\n')
                else:
                    console.print(message)
                continue  # Skip unsupported or unreadable files
            text_tuples.append((fp, text_content))

        # Process files sequentially
        data_images = process_image_files(image_files, image_inference, text_inference, silent=silent_mode, log_file=log_file)
        data_texts = process_text_files(text_tuples, text_inference, silent=silent_mode, log_file=log_file)

        # Prepare for copying and renaming
        renamed_files = set()
        processed_files = set()

        # Process audio files
        data_audio = process_audio_files(audio_files, audio_inference, silent=silent_mode, log_file=log_file)

        # Combine all data
        all_data = data_images + data_texts + data_audio



        # Compute the operations
        operations = compute_operations(
            all_data,
            output_dir,
            renamed_files,
            processed_files
        )

    elif mode == Mode.DATE:
        # Process files by date
        operations = process_files_by_date(file_paths, output_dir, dry_run=dry_run, silent=silent_mode, log_file=log_file)
    elif mode == Mode.TYPE:
        # Process files by type
        operations = process_files_by_type(file_paths, output_dir, dry_run=dry_run, silent=silent_mode, log_file=log_file)
    else:
        console.print("Invalid mode selected.")
        return

    # Simulate and display the proposed directory tree
    console.print("-" * 50)
    console.print("Proposed directory structure:")
    console.print(os.path.abspath(output_dir))
    simulated_tree = simulate_directory_tree(operations, output_dir)
    print_simulated_tree(simulated_tree)
    console.print("-" * 50)

    # Create the output directory now
    os.makedirs(output_dir, exist_ok=True)

    # Perform the actual file operations
    console.print("Performing file operations...")
    execute_operations(
        operations,
        dry_run=dry_run,
        silent=silent_mode,
        log_file=log_file
    )

    console.print("The files have been organized successfully.")
    console.print("-" * 50)


if __name__ == '__main__':
    main()
