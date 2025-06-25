from adk.llm_agent import LlmAgent, LlmAgentConfig, UserMessage, AssistantMessage
from adk.llm_service_adapter import LlmServiceAdapter
from adk.session import Session

class RegulationsAgent(LlmAgent):
    """
    RegulationsAgent checks the proposed design against simplified building regulations/codes.
    It analyzes the DesignAgent’s output for compliance issues and either approves it
    or outputs required modifications.
    """

    def __init__(self, llm_service_adapter: LlmServiceAdapter | None = None):
        config = LlmAgentConfig(
            name="RegulationsAgent",
            # instructions are now typically part of the initial messages or prompt template
        )
        super().__init__(config=config, llm_service_adapter=llm_service_adapter)

    async def check_compliance(self, session: Session, design_proposal: str) -> str:
        """
        Checks the design proposal for compliance with simplified regulations.
        Returns an approval message or a list of required modifications.
        """
        # Simplified regulations for this example
        regulations_summary = """
Simplified Building Regulations Checklist:
1. Minimum Room Sizes:
   - Bedrooms: At least 7.5 sqm. Master bedroom at least 10 sqm.
   - Living Room: At least 15 sqm.
   - Kitchen: At least 5 sqm.
2. Ceiling Height: Minimum 2.4 meters for habitable rooms. (Assume standard if not specified in design)
3. Natural Light/Ventilation: All habitable rooms (bedrooms, living rooms) should have access to natural light (e.g., windows). (Assume design implies this if not explicitly denied)
4. Safety:
   - Balconies must have railings (assume designed if "balcony" is mentioned).
   - Clear evacuation paths (conceptual: avoid designs that seem to block exits).
5. Accessibility: (Simplified) At least one entrance should be accessible without steps. (May not be checkable from conceptual design).

Based on the design proposal, identify any potential violations of these simplified regulations.
If all clear, state "Design Approved".
If there are issues, state "Design Requires Modification" and list the specific issues and suggestions.
Focus only on these simplified regulations.
        """

        prompt_template = f"""
You are an AI building regulations checker. Your task is to analyze the following conceptual
design proposal against a simplified set of building codes.

Conceptual Design Proposal:
{design_proposal}

Regulations Summary:
{regulations_summary}

Your Compliance Check (respond with "Design Approved" or "Design Requires Modification" followed by details):
        """

        messages = [
            UserMessage(content=prompt_template)
        ]

        response_message = await self.invoke(session, messages)

        if response_message and isinstance(response_message.content, str):
            # Simulate RegulationsAgent adding its response to the session state
            session.set_agent_state(self.config.name, {"compliance_check_result": response_message.content})
            session.add_message(AssistantMessage(content=response_message.content, name=self.config.name))
            return response_message.content
        elif response_message:
            content_str = str(response_message.content)
            session.set_agent_state(self.config.name, {"compliance_check_result": content_str})
            session.add_message(AssistantMessage(content=content_str, name=self.config.name))
            return content_str

        return "Error: Could not perform compliance check."

if __name__ == '__main__':
    import asyncio
    from dotenv import load_dotenv
    # from adk.llm_service_adapters.gemini_adapter import GeminiAdapter

    load_dotenv()

    async def main():
        # regulations_agent = RegulationsAgent(llm_service_adapter=GeminiAdapter())
        regulations_agent = RegulationsAgent() # Uses default
        test_session = Session(session_id="test_regulations_agent")

        sample_design_proposal_compliant = """
Conceptual Design Proposal:
The house is a two-story modern building.
Ground Floor: Features a spacious living room (approx. 25 sqm) connected to an open-plan kitchen (approx. 10 sqm).
There's also a small guest bathroom. Large windows provide ample natural light.
First Floor: Contains three bedrooms. The master bedroom (approx. 15 sqm) has an en-suite bathroom and access to a balcony with railings.
The other two bedrooms are smaller (approx. 8 sqm and 9 sqm respectively). A shared bathroom is also on this floor.
All rooms have standard ceiling heights and windows.
        """

        sample_design_proposal_non_compliant = """
Conceptual Design Proposal:
This is a compact single-story home.
It has a combined living area and kitchen (total 12 sqm).
There are two small bedrooms, one is 6 sqm and the other is 7 sqm.
No mention of windows in bedrooms, but it has a door to the garden.
        """
        print(f"Testing Compliant Design:\n{sample_design_proposal_compliant}\n")
        compliance_result_1 = await regulations_agent.check_compliance(test_session, sample_design_proposal_compliant)
        print("Compliance Check Result 1:")
        print(compliance_result_1)
        # print(f"Session state: {test_session.get_agent_state(regulations_agent.config.name)}")

        print(f"\nTesting Non-Compliant Design:\n{sample_design_proposal_non_compliant}\n")
        # New session for a clean test or clear history
        test_session_2 = Session(session_id="test_regulations_agent_2")
        compliance_result_2 = await regulations_agent.check_compliance(test_session_2, sample_design_proposal_non_compliant)
        print("Compliance Check Result 2:")
        print(compliance_result_2)
        # print(f"Session state: {test_session_2.get_agent_state(regulations_agent.config.name)}")


    # asyncio.run(main()) # Comment out for non-blocking tool execution
    pass
