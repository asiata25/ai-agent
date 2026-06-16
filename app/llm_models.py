import os

from agents.extensions.models.any_llm_model import AnyLLMModel
from dotenv import load_dotenv


load_dotenv()


model = AnyLLMModel(
	api_key=os.environ["API_KEY"],
	base_url=os.environ["API_URL"],
	model="MiniMax-M2.7-highspeed",
)