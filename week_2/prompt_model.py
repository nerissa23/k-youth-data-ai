import os
import sys
from google import genai
from google.genai import errors
from ollama import generate
from dotenv import load_dotenv

# getting google api key from .env file
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def ollama_prompt(model: str, prompt: str) -> str:
    """Use `ollama.generate()` to run one-shot prompts with ollama model"""

    try:
        res = generate(
            model=model,
            prompt=prompt
        )
        return res.response
    except Exception as e:
        return f"[Ollama Error] {e}"

def gemini_prompt(model: str, prompt: str) -> str:
    """Run gemini model specified to generate content"""

    try:
        if not API_KEY:
            return f"[Gemini Error] No API key found"
        client = genai.Client(api_key=API_KEY)
        res = client.models.generate_content(
            model=model,
            contents=prompt
        )
        return res.text
    except errors.APIError as e:
        return f"[Gemini Error] {e.code} {e.status}. {e}"
    except Exception as e:
        return f"{type(e).__name__}: {e}"

def prompt_model(model: str, prompt: str) -> str :
    """Use model selected to generate content from text prompt;
    Returns text response"""

    # check if prompt is valid: truthy strings
    if not prompt.strip():
        return "Please enter a proper text prompt."
    
    ollama_models = ['deepseek-r1:1.5b', 'phi3', 'llama3.1']
    google_models = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-3-flash-preview']

    # if model --> ollama models:
    if any(elem in model for elem in ollama_models):
        res = ollama_prompt(model, prompt)

    # if model --> google/gemini models:
    elif any(elem in model for elem in google_models):
        res = gemini_prompt(model, prompt)

    else:
        return f"Model selected is not available. Please select any of the following models: \n--> ollama models -> {ollama_models} \n--> google models -> {google_models}"
    
    return res

def main():
    # strictly enforce only 2 args to pass into prompt_model()
    if len(sys.argv) == 3:
        model_name = sys.argv[1]
        text_prompt = sys.argv[2]
        response = prompt_model(model_name, text_prompt)
        print("\n--- RESPONSE ---\n")
        if response: print(response)
    else:
        print("Usage: uv run prompt_model.py [model-name] [text-prompt]")

if __name__ == "__main__":
    main()