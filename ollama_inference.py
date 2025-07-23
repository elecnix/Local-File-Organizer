import ollama
import base64

class OllamaTextInference:
    def __init__(self, model_name="llama3"): # Default to llama3, can be configured
        self.model_name = model_name

    def generate(self, prompt):
        response = ollama.generate(model=self.model_name, prompt=prompt)
        return response['response']

class OllamaVLMInference:
    def __init__(self, model_name="llava"): # Default to llava, can be configured
        self.model_name = model_name

    def generate_vision(self, prompt, image_path):
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        response = ollama.generate(model=self.model_name, prompt=prompt, images=[image_data])
        return response['response']
