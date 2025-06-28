from .patched_lite_llm import PatchedLiteLlm
from config import LLM_API_BASE_URL, LLM_API_KEY

# Preconfigured model instance
gpt4o_mini = PatchedLiteLlm(
    model="openai/openai/gpt-4o-mini",
    api_base=LLM_API_BASE_URL,
    api_key=LLM_API_KEY,
)
