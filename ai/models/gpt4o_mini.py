from google.adk.models.lite_llm import LiteLlm
from config import LLM_API_BASE_URL, LLM_API_KEY

# Preconfigured model instance
gpt4o_mini = LiteLlm(
    model="openai/openai/o4-mini",
    api_base=LLM_API_BASE_URL,
    api_key=LLM_API_KEY,
)
