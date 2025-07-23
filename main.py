import os
import time
import argparse
import sys
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

from output_filter import filter_specific_output  # Import the context manager
try:
    from ollama_inference import OllamaVLMInference, OllamaTextInference # Import Ollama inference classes
    ollama_available = True
except Exception as e:
    print(f"Warning: Ollama client not available. AI-powered content organization will be disabled. Error: {e}")
    ollama_available = False

def ensure_nltk_data():
    """Ensure that NLTK data is downloaded efficiently and quietly."""
    import nltk
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)

# Initialize models
image_inference = None
text_inference = None

def initialize_models():
    """Initialize the models if they haven't been initialized yet."""
    global image_inference, text_inference
    if ollama_available and (image_inference is None or text_inference is None):

        # Use the filter_specific_output context manager
        with filter_specific_output():
            # Initialize the image inference model
            image_inference = OllamaVLMInference(
                model_name="llava"
            )

            # Initialize the text inference model
            text_inference = OllamaTextInference(
                model_name="llama3"
            )
        print("**----------------------------------------------**")
        print("**       Image inference model initialized      **")
    elif not ollama_available:
        print("AI models not initialized because Ollama client is not available.")
        print("**       Text inference model initialized       **")
        print("**----------------------------------------------**")

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

def get_yes_no(prompt):
    """Prompt the user for a yes/no response."""
    while True:
        response = input(prompt).strip().lower()
        if response in ('yes', 'y'):
            return True
        elif response in ('no', 'n'):
            return False
        elif response == '/exit':
            print("Exiting program.")
            exit()
        else:
            print("Please enter 'yes' or 'no'. To exit, type '/exit'.")

def get_mode_selection():
    """Prompt the user to select a mode."""
    while True:
        print("Please choose the mode to organize your files:")
        if ollama_available:
            print("1. By Content")
        print("2. By Date")
        print("3. By Type")
        response = input("Enter 1, 2, or 3 (or type '/exit' to exit): ").strip()
        if response == '/exit':
            print("Exiting program.")
            exit()
        elif response == '1':
            if ollama_available:
                return 'content'
            else:
                print("Invalid selection. 'By Content' mode is not available because Ollama client is not available.")
        elif response == '2':
            return 'date'
        elif response == '3':
            return 'type'
        else:
            print("Invalid selection. Please enter 1, 2, or 3. To exit, type '/exit'.")

def main():
    parser = argparse.ArgumentParser(description="Organize files based on content, date, or type.")
    parser.add_argument("--input_dir", type=str, required=True, help="Path of the directory to organize.")
    parser.add_argument("--output_dir", type=str, default="", help="Path to store organized files and folders (default: 'organized_folder' in input directory).")
    parser.add_argument("--mode", type=int, choices=[1, 2, 3], required=True, help="Mode to organize files: 1 (By Content), 2 (By Date), 3 (By Type).")
    parser.add_argument("--silent", type=str, choices=["yes", "no"], default="no", help="Enable silent mode (yes/no).")

    args = parser.parse_args()

    console = Console()

    silent_mode = args.silent == 'yes'

    log_file = None
    if silent_mode:
        log_file_path = os.path.join(os.getcwd(), "log.txt")
        log_file = open(log_file_path, "w")
        sys.stdout = log_file
        sys.stderr = log_file

    input_dir = args.input_dir
    console.print(f"Input path successfully uploaded: {input_dir}")
    console.print("--------------------------------------------------")

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(input_dir, "organized_folder")
    console.print(f"Output path successfully set to: {output_dir}")
    console.print("--------------------------------------------------")

    # Ensure NLTK data is downloaded efficiently and quietly
    ensure_nltk_data()

    # Start with dry run set to True
    dry_run = True

    start_time = time.time()
    file_paths = collect_file_paths(input_dir)
    end_time = time.time()

    console.print(f"Time taken to load file paths: {end_time - start_time:.2f} seconds")
    console.print("--------------------------------------------------")
    console.print("Directory tree before organizing:")
    display_directory_tree(input_dir)

    console.print("**************************************************")

    mode = args.mode
    operations = []

    if mode == 1:
        # Proceed with content mode
        if not silent_mode:
            console.print("Checking if the model is already downloaded. If not, downloading it now.")
        initialize_models()

        if not silent_mode:
            console.print("**************************************************")
            console.print("The file upload was successful. Processing may take a few minutes.")
            console.print("**************************************************")

        # Separate files by type
        image_files, text_files = separate_files_by_type(file_paths)

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

        # Combine all data
        all_data = data_images + data_texts

        # Compute the operations
        operations = compute_operations(
            all_data,
            output_dir,
            renamed_files,
            processed_files
        )

    elif mode == 2:
        # Process files by date
        operations = process_files_by_date(file_paths, output_dir, dry_run=dry_run, silent=silent_mode, log_file=log_file)
    elif mode == 3:
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
