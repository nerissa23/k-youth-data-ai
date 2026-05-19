import os
import sys
from google import genai
from google.genai import errors
from ollama import generate
from dotenv import load_dotenv

# getting google api key from .env file
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def prompt_model(model: str, prompt: str) -> str :
    """Use model selected to generate content from text prompt;
    Returns text response"""

    # check if prompt is valid: truthy strings
    if not prompt:
        return f"Please enter a proper text prompt."
    
    ollama_models = ['deepseek-r1:1.5b', 'phi3', 'llama3.1']

    try:
        # if model --> ollama models:
        if any(elem in model for elem in ollama_models):
            res = generate(
                model=model,
                prompt=prompt
            )
            print("\n--- RESPONSE ---\n")
            return res.response

        # if model --> google/gemini models:
        client = genai.Client(api_key=API_KEY)
        res = client.models.generate_content(
            model=model,
            contents=prompt
        )
        print("\n--- RESPONSE ---\n")
        return res.text
    except errors.APIError as e:
        # catch errors returned by google's api server
        print(f"[Gemini Error] {e.code} {e.status}. {e}")
    except Exception as e:
        print(f"Function error: {e}")

def main():
    # strictly enforce only 2 args to pass into prompt_model()
    if len(sys.argv) == 3:
        model_name = sys.argv[1]
        text_prompt = sys.argv[2]
        response = prompt_model(model_name, text_prompt)
        if response: print(response)
    else:
        print("Usage: uv run prompt_model.py [model-name] [text-prompt]")

if __name__ == "__main__":
    main()