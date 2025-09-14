from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.constants import MODEL_GEMINI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')


model_info={
        "json_output": True,
        "function_calling": True,
        "vision": True,
        "family": "unknown",
        "structured_output": True,
    }


def get_model_client():
    openai_model_client = OpenAIChatCompletionClient(
        model=MODEL_GEMINI,
        api_key=api_key,
        model_info = model_info 
    )

    return openai_model_client
