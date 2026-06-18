from agents.extensions.models.any_llm_model import AnyLLMModel
from app.core.settings import settings


model = AnyLLMModel(
	api_key=settings.api_key,
	base_url=settings.api_url,
	model="MiniMax-M2.7-highspeed",
)