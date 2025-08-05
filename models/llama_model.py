import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LlamaModel:
    """
    A class to interact with the LLaMA 2 model via the Hugging Face Inference API.
    This avoids loading the model locally, saving significant system resources.
    """
    def __init__(self, model_name: str = "meta-llama/Llama-2-7b-chat-hf"):
        """
        Initializes the API client for the specified LLaMA 2 model.
        
        Args:
            model_name (str): The identifier for the model on Hugging Face Hub.
        """
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.api_token = os.getenv("HUGGING_FACE_TOKEN")
        
        if not self.api_token:
            raise ValueError("HUGGING_FACE_TOKEN is not set in the .env file.")
            
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        print(f"API client initialized for model: {model_name}")

    def run(self, prompt: str) -> str:
        """
        Sends a prompt to the Inference API and gets a response.
        
        Args:
            prompt (str): The input prompt for the model.
            
        Returns:
            str: The model's generated response (hopefully a JSON string).
        """
        print("\n--- Sending Prompt to LLaMA 2 Inference API ---")
        
        # The API expects a JSON payload with the 'inputs' key
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "return_full_text": False, # Important to get only the generated part
            }
        }
        
        response = None # Initialize response to None
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=90)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            api_response = response.json()
            print("--- Raw API Response ---")
            print(api_response)

            # Extract the generated text
            generated_text = api_response[0].get("generated_text", "")
            
            # Find and return the clean JSON part
            json_start_index = generated_text.find('{')
            if json_start_index != -1:
                json_end_index = generated_text.rfind('}')
                if json_end_index != -1:
                    clean_response = generated_text[json_start_index : json_end_index + 1]
                    print("\n--- Cleaned JSON Response ---")
                    print(clean_response)
                    return clean_response
            
            return '{"error": "Could not extract a valid JSON object from the API response."}'

        except requests.exceptions.RequestException as e:
            print(f"--- Error calling Inference API ---")
            print(f"Exception Type: {type(e)}")
            print(f"Error Message: {e}")
            
            if response is not None:
                print(f"Response Status Code: {response.status_code}")
                print(f"Response Text: {response.text}")
                error_details = response.text.replace('"', '\\"')
            else:
                error_details = "No response from server. Check network connection/firewall."

            return f'{{"error": "API request failed.", "details": "{error_details}"}}'

# Create a single instance to be imported elsewhere
llm_model = LlamaModel()
