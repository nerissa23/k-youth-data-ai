import os
import sys
from google import genai
from google.genai import errors, types
from ollama import Client
from dotenv import load_dotenv
from dataclasses import dataclass

# getting google api key from .env file
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

OLLAMA_MODELS = ["deepseek-r1:1.5b", "phi3", "llama3.1", "gemma3:1b"]
GOOGLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
]


@dataclass
class ModelConfig:
    temperature: float = 0.7
    seed: int | None = None


def ollama_prompt(model: str, prompt: str, config: ModelConfig | None = None) -> str:
    """Use `ollama.generate()` to run one-shot prompts with ollama model"""

    try:
        options = {}
        if config:
            options["temperature"] = config.temperature
            if config.seed is not None:
                options["seed"] = config.seed

        host = os.getenv("OLLAMA_HOST")
        client = Client(host=host)

        res = client.generate(
            model=model, prompt=prompt, options=options if options else None
        )
        return res.response
    except Exception as e:
        return f"[Ollama Error] {e}"


def gemini_prompt(model: str, prompt: str, config: ModelConfig | None = None) -> str:
    """Run gemini model specified to generate content"""

    if not API_KEY:
        return "[Error] GOOGLE_API_KEY not set in week_2/.env"

    try:
        client = genai.Client(api_key=API_KEY)

        gemini_config = None
        if config:
            gemini_config = types.GenerateContentConfig(
                temperature=config.temperature,
                **({"seed": config.seed} if config.seed is not None else {}),
            )

        res = client.models.generate_content(
            model=model,
            contents=prompt,
            **({"config": gemini_config} if gemini_config else {}),
        )
        return res.text
    except errors.APIError as e:
        if e.code == 429:
            return f"[Gemini Error] RateLimitError: {e}"
        return f"[Gemini Error] {e.code} {e.status}. {e}"
    except Exception as e:
        return f"[Error] {type(e).__name__}: {e}"


def prompt_model(model: str, prompt: str, config: ModelConfig | None = None) -> str:
    """Use model selected to generate content from text prompt;
    Returns text response"""

    model = model.strip()
    prompt = prompt.strip()

    model_selection_guide = f"Please select any of the following models: \n--> ollama models -> {OLLAMA_MODELS} \n--> google models -> {GOOGLE_MODELS}"

    if not model:
        return f"[Error] {model_selection_guide}"
    if not prompt:
        return "[Error] Please enter a proper text prompt."

    # if model --> ollama models:
    if any(elem in model for elem in OLLAMA_MODELS):
        return ollama_prompt(model, prompt, config)
    # if model --> google/gemini models:
    elif any(elem in model for elem in GOOGLE_MODELS):
        return gemini_prompt(model, prompt, config)
    else:
        return f"[Error] Model selected is not available. {model_selection_guide}"


def main():
    # strictly enforce only 2 args to pass through command
    args = sys.argv[1:]
    if len(args) == 2:
        model = args[0]
        prompt = args[1]
        response = prompt_model(model, prompt)
        print("\n--- RESPONSE ---\n")
        if response:
            print(response)
    else:
        print("Usage: uv run prompt_model.py <model> <prompt>")


if __name__ == "__main__":
    main()
