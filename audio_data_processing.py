import os
import torch
import whisper
import json
from data_processing_common import sanitize_filename

from rich.console import Console

console = Console()

# Global variable for the Whisper model
WHISPER_MODEL = None

def initialize_whisper_model(model_size="base", device="cuda" if torch.cuda.is_available() else "cpu", silent=False):
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        if not silent:
            console.print(f"[bold yellow]Initializing Whisper model ({model_size}) on {device} device...[/bold yellow]")
        try:
            WHISPER_MODEL = whisper.load_model(model_size, device=device)
            if not silent:
                console.print("[bold green]Whisper model initialized successfully![/bold green]")
        except Exception as e:
            if not silent:
                console.print(f"[bold red]Error initializing Whisper model: {e}[/bold red]")
            WHISPER_MODEL = None

def transcribe_audio_with_whisper(audio_path, silent=False):
    if WHISPER_MODEL is None:
        if not silent:
            console.print("[bold red]Whisper model not initialized. Please call initialize_whisper_model first.[/bold red]")
        return None

    if not silent:
        console.print(f"[bold blue]Transcribing audio file: {audio_path}...[/bold blue]")
    try:
        result = WHISPER_MODEL.transcribe(audio_path)
        transcription = result["text"]
        if not silent:
            console.print(f"[bold green]Transcription complete for {os.path.basename(audio_path)}.[/bold green]")
        return transcription
    except Exception as e:
        if not silent:
            console.print(f"[bold red]Error transcribing audio file {audio_path}: {e}[/bold red]")
        return None


def process_audio_file_for_ollama(audio_path, ollama_inference_function, silent=False, log_file=None):
    transcription = transcribe_audio_with_whisper(audio_path, silent=silent)
    if transcription:
        if not silent:
            console.print(f"[bold cyan]Sending transcription to Ollama for inference: {transcription[:50]}...[/bold cyan]")
        try:
            # Prompt Ollama to generate description, folder name, and filename in JSON format
            prompt = f"""Analyze the following audio transcription and provide a concise description, a suitable folder name (max 2 words, nouns only), and a descriptive filename (max 3 words, nouns only, underscores for spaces). Return the output as a JSON object with keys 'description', 'foldername', and 'filename'.

Example:
Transcription: This is a recording of a dog barking loudly in a park.
JSON Output: {{ "description": "Recording of a dog barking in a park", "foldername": "animal_sounds", "filename": "dog_barking_park" }}

Transcription: {transcription}

JSON Output:"""

            ollama_result = ollama_inference_function.generate(prompt)
            
            # Parse the JSON result
            try:
                parsed_result = json.loads(ollama_result)
                description = parsed_result.get('description', '').strip()
                foldername = sanitize_filename(parsed_result.get('foldername', '').strip())
                filename = sanitize_filename(parsed_result.get('filename', '').strip())
            except json.JSONDecodeError:
                description = f"Transcription of {os.path.basename(audio_path)}"
                foldername = "audio_transcriptions"
                filename = sanitize_filename(f"audio_{os.path.basename(audio_path).split('.')[0]}")
            if not silent:
                console.print("[bold green]Ollama inference complete.[/bold green]")
            return {
                'file_path': audio_path,
                'transcription': transcription,
                'description': description,
                'foldername': foldername,
                'filename': filename
            }
        except Exception as e:
            message = f"Error during Ollama inference for {audio_path}: {e}"
            if silent:
                if log_file:
                    log_file.write(message + '\n')
            else:
                console.print(f"[bold red]{message}[/bold red]")
            return None
    return None

def process_audio_files(audio_files, ollama_inference_function, silent=False, log_file=None):
    processed_data = []
    for audio_file in audio_files:
        data = process_audio_file_for_ollama(audio_file, ollama_inference_function, silent, log_file)
        if data:
            processed_data.append(data)
    return processed_data
