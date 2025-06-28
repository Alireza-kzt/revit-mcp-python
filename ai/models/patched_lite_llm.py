from google.adk.models.lite_llm import LiteLlm


def _ensure_content(messages):
    """Ensure each message includes a content field."""
    for msg in messages:
        if isinstance(msg, dict) and "tool_calls" in msg and "content" not in msg:
            msg["content"] = ""


class PatchedLiteLlm(LiteLlm):
    """LiteLlm subclass that adds empty content when missing."""

    async def acompletion(self, **kwargs):
        messages = kwargs.get("messages")
        if messages:
            _ensure_content(messages)
        return await super().acompletion(**kwargs)

    def completion(self, **kwargs):
        messages = kwargs.get("messages")
        if messages:
            _ensure_content(messages)
        return super().completion(**kwargs)

