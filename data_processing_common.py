import os
import datetime  # Import datetime for date operations
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from image_data_processing import get_date_from_exif, extract_date_from_filename # Import date extraction functions
from file_utils import sanitize_filename # Import sanitize_filename from file_utils

def process_files_by_date(file_paths, output_path, dry_run=False, silent=False, log_file=None):
    """Process files to organize them by date."""
    operations = []
    for file_path in file_paths:
        # Get the modification time
        mod_time = os.path.getmtime(file_path)
        # Convert to datetime
        mod_datetime = datetime.datetime.fromtimestamp(mod_time)
        year = mod_datetime.strftime('%Y')
        month = mod_datetime.strftime('%B')  # e.g., 'January', or use '%m' for month number
        # Create directory path
        dir_path = os.path.join(output_path, year, month)
        # Prepare new file path
        new_file_name = os.path.basename(file_path)
        new_file_path = os.path.join(dir_path, new_file_name)
        # Decide whether to use hardlink or symlink
        link_type = 'hardlink'  # Assume hardlink for now
        # Record the operation
        operation = {
            'source': file_path,
            'destination': new_file_path,
            'link_type': link_type,
        }
        operations.append(operation)
    return operations

def process_files_by_type(file_paths, output_path, dry_run=False, silent=False, log_file=None):
    """Process files to organize them by type, first separating into text-based and image-based files."""
    operations = []

    # Define extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')
    text_extensions = ('.txt', '.md', '.docx', '.doc', '.pdf', '.xls', '.xlsx', '.epub', '.mobi', '.azw', '.azw3')

    for file_path in file_paths:
        # Exclude hidden files (additional safety)
        if os.path.basename(file_path).startswith('.'):
            continue

        # Get the file extension
        ext = os.path.splitext(file_path)[1].lower()

        # Check if it's an image file
        if ext in image_extensions:
            # Image-based files
            top_folder = 'image_files'
            # You can add subcategories here if needed
            folder_name = top_folder

        elif ext in text_extensions:
            # Text-based files
            top_folder = 'text_files'
            # Map extensions to subfolders
            if ext in ('.txt', '.md'):
                sub_folder = 'plain_text_files'
            elif ext in ('.doc', '.docx'):
                sub_folder = 'doc_files'
            elif ext == '.pdf':
                sub_folder = 'pdf_files'
            elif ext in ('.xls', '.xlsx'):
                sub_folder = 'xls_files'
            elif ext in ('.epub', '.mobi', '.azw', '.azw3'):
                sub_folder = 'ebooks'
            else:
                sub_folder = 'others'
            folder_name = os.path.join(top_folder, sub_folder)

        else:
            # Other types
            folder_name = 'others'

        # Create directory path
        dir_path = os.path.join(output_path, folder_name)
        # Prepare new file path
        new_file_name = os.path.basename(file_path)
        new_file_path = os.path.join(dir_path, new_file_name)
        # Decide whether to use hardlink or symlink
        link_type = 'hardlink'  # Assume hardlink for now
        # Record the operation
        operation = {
            'source': file_path,
            'destination': new_file_path,
            'link_type': link_type,
        }
        operations.append(operation)

    return operations

def compute_operations(data_list, new_path, renamed_files, processed_files, prefix_dates=False):
    """Compute the file operations based on generated metadata."""
    operations = []
    for data in data_list:
        file_path = data['file_path']
        if file_path in processed_files:
            continue
        processed_files.add(file_path)

        # Prepare folder name and file name
        folder_name = data['foldername']
        base_filename = data['filename']
        file_extension = os.path.splitext(file_path)[1]

        # Apply date prefixing if enabled (logic moved from execute_operations)
        # This ensures the simulated tree also reflects the date prefix
        date_prefix = None
        exif_date = get_date_from_exif(file_path)
        if exif_date:
            date_prefix = exif_date
        else:
            filename_only = os.path.basename(file_path)
            date_from_filename = extract_date_from_filename(filename_only)
            if date_from_filename != "null":
                date_prefix = date_from_filename

        if prefix_dates and date_prefix:
            new_file_name = f"{date_prefix}_{base_filename}{file_extension}"
        else:
            new_file_name = f"{base_filename}{file_extension}"

        # Prepare new file path
        dir_path = os.path.join(new_path, folder_name)
        new_file_path = os.path.join(dir_path, new_file_name)

        # Handle duplicates
        counter = 1
        while new_file_path in renamed_files:
            new_file_name = f"{data['filename']}_{counter}" + os.path.splitext(file_path)[1]
            new_file_path = os.path.join(dir_path, new_file_name)
            counter += 1

        # Decide whether to use hardlink or symlink
        link_type = 'hardlink'  # Assume hardlink for now

        # Record the operation
        operation = {
            'source': file_path,
            'destination': new_file_path,
            'link_type': link_type,
            'folder_name': folder_name,
            'new_file_name': new_file_name,
            'prefix_dates': True if date_prefix else False # Indicate if date prefix was applied
        }
        operations.append(operation)
        renamed_files.add(new_file_path)

    return operations  # Return the list of operations for display or further processing

def execute_operations(operations, dry_run=False, silent=False, log_file=None, prefix_dates=False):
    """Execute the file operations."""
    total_operations = len(operations)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True
    ) as progress:
        task = progress.add_task("Organizing Files...", total=total_operations)
        for operation in operations:
            source = operation['source']
            destination = operation['destination']
            link_type = operation['link_type']
            dir_path = os.path.dirname(destination)

            # The new_file_name already includes the date prefix if applicable
            new_file_name = operation['new_file_name']
            destination = os.path.join(dir_path, os.path.basename(new_file_name))

            if dry_run:
                message = f"Dry run: would create {link_type} from '{source}' to '{destination}'"
            else:
                # Ensure the directory exists before performing the operation
                os.makedirs(dir_path, exist_ok=True)

                try:
                    if link_type == 'hardlink':
                        os.link(source, destination)
                    else:
                        os.symlink(source, destination)
                    message = f"Created {link_type} from '{source}' to '{destination}'"
                except Exception as e:
                    message = f"Error creating {link_type} from '{source}' to '{destination}': {e}"

            progress.advance(task)

            # Silent mode handling
            if silent:
                if log_file:
                    with open(log_file, 'a') as f:
                        f.write(message + '\n')
            else:
                print(message)