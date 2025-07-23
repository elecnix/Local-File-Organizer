# Local File Organizer: AI File Management Run Entirely on Your Device, Privacy Assured

Tired of digital clutter? Overwhelmed by disorganized files scattered across your computer? Let AI do the heavy lifting! The Local File Organizer is your personal organizing assistant, using cutting-edge AI to bring order to your file chaos - all while respecting your privacy.

## How It Works 💡

Before:

```
/home/user/messy_documents/
├── IMG_20230515_140322.jpg
├── IMG_20230516_083045.jpg
├── IMG_20230517_192130.jpg
├── budget_2023.xlsx
├── meeting_notes_05152023.txt
├── project_proposal_draft.docx
├── random_thoughts.txt
├── recipe_chocolate_cake.pdf
├── scan0001.pdf
├── vacation_itinerary.docx
└── work_presentation.pptx

0 directories, 11 files
```

After:

```
/home/user/organized_documents/
├── Financial
│   └── 2023_Budget_Spreadsheet.xlsx
├── Food_and_Recipes
│   └── Chocolate_Cake_Recipe.pdf
├── Meetings_and_Notes
│   └── Team_Meeting_Notes_May_15_2023.txt
├── Personal
│   └── Random_Thoughts_and_Ideas.txt
├── Photos
│   ├── Cityscape_Sunset_May_17_2023.jpg
│   ├── Morning_Coffee_Shop_May_16_2023.jpg
│   └── Office_Team_Lunch_May_15_2023.jpg
├── Travel
│   └── Summer_Vacation_Itinerary_2023.docx
└── Work
    ├── Project_X_Proposal_Draft.docx
    ├── Quarterly_Sales_Report.pdf
    └── Marketing_Strategy_Presentation.pptx

7 directories, 11 files
```

## Updates 🚀

**[July 2025] v0.0.3**:
* **Visual Interpretation of PDFs**: Extracts images from PDF files and uses a vision model to interpret their content, enhancing the overall understanding of PDF documents.
* **Full Audio File Support**: Transcribe audio using Whisper and organize based on content using Ollama.
* **Ollama Integration Enhanced**: Fully transitioned to Ollama for all AI processing (text, image, and audio), removing all Nexa dependencies.
* **Improved Argument Handling**: `--input_dir` and `--input_file` are now mutually exclusive and required.
* **Image Filename Date Prefixing**: Automatically prefixes image filenames with dates extracted from EXIF data, filenames, or LLM fallback, ensuring accurate and consistent dating.

**[September 2024] v0.0.2**:
* Now powered by Ollama for local AI processing!
* Dry Run Mode: check sorting results before committing changes
* Silent Mode: save all logs to a txt file for quieter operation
* Added file support:  `.md`, `.xlsx`, `.pptx`, and `.csv` 
* Three sorting options: by content (Mode 1), by date (Mode 2), and by type (Mode 3).
* Improved CLI interaction experience
* Added real-time progress bar for file analysis

To update the project, navigate to the project directory and run `git pull`. Then, reinstall the dependencies as described in the Installation section.


## Roadmap 📅

- [ ] Copilot Mode: chat with AI to tell AI how you want to sort the file (ie. read and rename all the PDFs)
- [ ] Change models with CLI 
- [ ] ebook format support
- [x] audio file support
- [ ] video file support
- [ ] Implement best practices like Johnny Decimal
- [ ] Check file duplication
- [ ] Dockerfile for easier installation

## What It Does 🔍

This intelligent file organizer harnesses the power of advanced AI models, including language models (LMs) and vision-language models (VLMs), to automate the process of organizing files by:


* Scanning a specified input directory for files.
* Content Understanding: 
  - **Textual Analysis**: Uses a local Llama 3 model (via Ollama) to analyze and summarize text-based content, generating relevant descriptions and filenames.
  - **Visual Content Analysis**: Uses a local LLaVA model (via Ollama) to interpret visual files such as images, providing context-aware categorization and descriptions.

* Understanding the content of your files (text, images, and more) to generate relevant descriptions, folder names, and filenames.
* Organizing the files into a new directory structure based on the generated metadata.

The best part? All AI processing happens 100% on your local device using [Ollama](https://ollama.com/). No internet connection required, no data leaves your computer, and no AI API is needed - keeping your files completely private and secure.


## Supported File Types 📁

- **Images:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`
- **Audio:** `.mp3`, `.wav`, `.flac`
- **Text Files:** `.txt`, `.docx`, `.md`
- **Spreadsheets:** `.xlsx`, `.csv`
- **Presentations:** `.ppt`, `.pptx`
- **PDFs:** `.pdf`

## Prerequisites 💻

- **Operating System:** Compatible with Windows, macOS, and Linux.
- **Python Version:** Python 3.12 or later

- **Git:** For cloning the repository (or you can download the code as a ZIP file).

## Installation 🛠

> For SDK installation and model-related issues, please post on [here](https://github.com/NexaAI/nexa-sdk/issues).

### 1. Install Python

Before installing the Local File Organizer, make sure you have Python installed on your system. We recommend using Python 3.12 or later.

You can download Python from [the official website]((https://www.python.org/downloads/)).

Follow the installation instructions for your operating system.

### 2. Clone the Repository

Clone this repository to your local machine using Git:

```zsh
git clone https://github.com/QiuYannnn/Local-File-Organizer.git
```

Or download the repository as a ZIP file and extract it to your desired location.

### 3. Set Up the Python Environment

First, ensure you have `uv` installed. If not, you can install it with `curl -LsSf https://astral.sh/uv/install.sh | sh`.

Create a new virtual environment:

```zsh
uv venv
```

Activate the environment:

```zsh
source .venv/bin/activate
```

### 4. Install Ollama and Download Models

Download and install Ollama from [ollama.com](https://ollama.com/).

Once Ollama is installed, download the necessary models:

```bash
ollama pull llama3
ollama pull llava
```


### 5. Install Dependencies 

1. Ensure you are in the project directory:
   ```zsh
   cd path/to/Local-File-Organizer
   ```
   Replace `path/to/Local-File-Organizer` with the actual path where you cloned or extracted the project.

2. Install the required dependencies:
   ```zsh
   uv pip install -r requirements.txt
   ```

**Note:** If you encounter issues with any packages, install them individually:

```zsh
uv pip install Pillow pytesseract PyMuPDF python-docx ollama
```

With the environment activated and dependencies installed, run the script using:

### 6. Running the Script🎉

**Note:** For testing purposes, you can use the provided `sample_data` directory as your input. For example:

```zsh
uv run python main.py --input_dir ./sample_data --mode 1 --dry_run yes
```

By default, if `--output_dir` is not specified, files will be organized into a new folder named `organized_folder` within your input directory.

To run with your own files, replace `/path/to/your/files` with the actual path to your input directory.

```zsh
uv run python main.py --input_dir /path/to/your/files --mode 1 --dry_run yes
```

To perform actual file operations, set `--dry_run` to `no`:
```zsh
uv run python main.py --input_dir /path/to/your/files --output_dir /path/to/organized/files --mode 1 --dry_run no
```

Example for organizing by date:
```zsh
uv run python main.py --input_dir /path/to/your/files --mode 2
```

Example for organizing by type:
```zsh
uv run python main.py --input_dir /path/to/your/files --mode 3
```

Example for silent mode:
```zsh
uv run python main.py --input_dir /path/to/your/files --mode 1 --silent yes
```

Example for processing a single audio file:
```zsh
uv run python main.py --input_file /path/to/your/audio.mp3 --mode 1 --dry_run yes
```

## Notes

- **Ollama Models:**
  - The script uses `llama3` for text analysis and `llava` for image analysis.
  - Ensure these models are downloaded and running in Ollama.


- **Dependencies:**
  - **pytesseract:** Requires Tesseract OCR installed on your system.
    - **macOS:** `brew install tesseract`
    - **Ubuntu/Linux:** `sudo apt-get install tesseract-ocr`
    - **Windows:** Download from [Tesseract OCR Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - **PyMuPDF (fitz):** Used for reading PDFs.

- **Processing Time:**
  - Processing may take time depending on the number and size of files.
  - The script uses multiprocessing to improve performance.

- **Customizing Prompts:**
  - You can adjust prompts in `text_data_processing.py`, `image_data_processing.py`, and `audio_data_processing.py` to change how metadata is generated.

## License

This project is dual-licensed under the MIT License and Apache 2.0 License. You may choose which license you prefer to use for this project.

- See the [MIT License](LICENSE-MIT) for more details.
- See the [Apache 2.0 License](LICENSE-APACHE) for more details.