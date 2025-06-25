from adk.llm_agent import LlmAgent, LlmAgentConfig, UserMessage
from adk.llm_service_adapter import LlmServiceAdapter
from adk.session import Session

# Placeholder for a real LLM service adapter if needed,
# for now, we'll rely on ADK's default (e.g., Gemini if API key is set).
# from adk.llm_service_adapters.gemini_adapter import GeminiAdapter

class InputAgent(LlmAgent):
    """
    InputAgent gathers and preprocesses user requirements for the architectural design.
    It takes user prompts (desired room count, size, style, etc.) and outputs a structured brief.
    """

    def __init__(self, llm_service_adapter: LlmServiceAdapter | None = None):
        config = LlmAgentConfig(
            name="InputAgent",
            # instructions are now typically part of the initial messages or prompt template
        )
        super().__init__(config=config, llm_service_adapter=llm_service_adapter)

    async def process(self, session: Session, user_prompt: str) -> str:
        """
        Processes the user's design prompt and extracts structured requirements.
        """
        # In ADK v1.0, instructions are often part of the initial message history.
        # Or, you can construct a more complex prompt here.
        prompt_template = f"""
You are an AI assistant helping an architect. Your role is to take a user's free-form request
for a building design and structure it into a clear, itemized brief.

User's request: "{user_prompt}"

Extract the key requirements and present them as a structured list. For example:
- Building Type: (e.g., Residential House, Office Space)
- Total Area: (e.g., approx. 200 sqm)
- Number of Floors: (e.g., 2)
- Key Spaces:
    - Room Type 1: (e.g., Living Room, dimensions/area if specified, features)
    - Room Type 2: (e.g., Kitchen, style like 'open-concept', appliances if mentioned)
    - Number of Bedrooms: (e.g., 3)
    - Number of Bathrooms: (e.g., 2.5)
- Architectural Style: (e.g., Modern, Traditional, Minimalist)
- Specific Constraints/Preferences: (e.g., Needs a home office, prefers natural light, budget considerations if mentioned)

If some information is not provided, note it as "Not specified".
Focus on extracting information relevant to architectural design.

Structured Brief:
        """

        # Add the system/instructional prompt and the user message to the session
        # In a more complex scenario, these could be pre-set in the session by an orchestrator.
        # For a direct call like this, we might just pass it to invoke.
        # session.add_message(Message(role="system", content=prompt_template.strip()))
        # response_message = await super().invoke(session, UserMessage(content=user_prompt))

        # With ADK v1.0, `invoke` is the primary method.
        # The prompt is constructed by passing a list of messages.
        # The "instructions" are usually the first system message.

        # Let's assume the Orchestrator will prepare the session with an initial system prompt.
        # For direct testing or if this agent is run standalone, we might do:
        # if not session.history: # Or some other check if instructions are needed
        # session.add_message(SystemMessage(content=self.config.instructions))

        # The process method is more abstract in BaseAgent.
        # For LlmAgent, we typically use `invoke` and the session's history.
        # Here, we are defining how this specific agent constructs its prompt.

        # We will use the `invoke` method of the LlmAgent.
        # The prompt construction will be handled by the agent based on its configuration
        # and the messages in the session.

        # For this agent, the "user_prompt" is the input to be processed.
        # We'll construct a message list for the LLM call.
        messages = [
            UserMessage(content=prompt_template)
        ]

        response_message = await self.invoke(session, messages)

        if response_message and isinstance(response_message.content, str):
            return response_message.content
        elif response_message:
            # Handle cases where content might be a list of parts (e.g. multimodal)
            # For now, we expect text.
            return str(response_message.content)
        return "Error: Could not generate a structured brief."

if __name__ == '__main__':
    import asyncio
    from dotenv import load_dotenv
    # This is a simple test, assuming GOOGLE_API_KEY is set in .env
    # from adk.llm_service_adapters.gemini_adapter import GeminiAdapter

    load_dotenv()

    async def main():
        # llm_adapter = GeminiAdapter() # Requires GOOGLE_API_KEY
        # input_agent = InputAgent(llm_service_adapter=llm_adapter)
        input_agent = InputAgent() # Uses default LLM service from ADK context

        test_session = Session(session_id="test_input_agent")

        user_query = "I want a two-story modern house, about 150 square meters. It should have 3 bedrooms, 2 bathrooms, a large kitchen, and a balcony. I love big windows."
        print(f"User Query: {user_query}\n")

        structured_brief = await input_agent.process(test_session, user_query)
        print("Structured Brief from InputAgent:")
        print(structured_brief)

    # asyncio.run(main()) # Commented out for non-blocking tool execution
    # To run this:
    # 1. Make sure you have a .env file with GOOGLE_API_KEY="..." or similar for your chosen LLM
    # 2. Uncomment asyncio.run(main())
    # 3. Run `python src/agents/input_agent.py`
    pass
