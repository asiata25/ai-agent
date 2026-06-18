import os
from dotenv import load_dotenv


load_dotenv()


def get_model() -> str:
    """
    Validate and retrieve OpenAI model configuration.

    Supports the API_KEY env var.

    Raises:
        RuntimeError: If API key is not set or model is invalid.

    Returns:
        Model identifier string.
    """
    api_key = os.getenv("API_KEY")

    if not api_key:
        raise RuntimeError(
            "API key not configured. Set API_KEY environment variable in .env"
        )

    model = "gpt-4.1-mini"
    return model
