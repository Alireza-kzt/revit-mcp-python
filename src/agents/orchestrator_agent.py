import asyncio
import os
import json
from typing import List, Dict, Any, Union

from adk.agent import Agent, AgentConfig
from adk.session import Session
from adk.message import Message, UserMessage, SystemMessage # SystemMessage might be useful
from adk.tool import ToolResponse, Call, ToolContext
from adk.mcp_toolset import MCPToolset

from .input_agent import InputAgent
from .design_agent import DesignAgent
from .regulations_agent import RegulationsAgent
from ..shared_models import DesignPlanModel, WallModel, RoomModel # Relative import

from dotenv import load_dotenv
load_dotenv() # Load .env file for FASTMCP_SERVER_URL and GOOGLE_API_KEY

FASTMCP_SERVER_URL = os.getenv("FASTMCP_SERVER_URL", "http://localhost:8765")

class OrchestratorAgentConfig(AgentConfig):
    name: str = "OrchestratorAgent"
    # description: str = "Orchestrates the architectural design process."

class OrchestratorAgent(Agent):
    """
    OrchestratorAgent oversees the architectural design process.
    It invokes InputAgent, DesignAgent (expects DesignPlanModel), and RegulationsAgent.
    If regulations feedback is OK, it uses MCPToolset to instruct Revit.
    """

    def __init__(self, config: OrchestratorAgentConfig = OrchestratorAgentConfig()):
        super().__init__(config)
        # Initialize sub-agents. ADK will use default LLM service if adapter is None.
        self.input_agent = InputAgent()
        self.design_agent = DesignAgent()
        self.regulations_agent = RegulationsAgent()

        self.mcp_toolset: MCPToolset | None = None

    async def process_design_request(self, session: Session, user_design_prompt: str) -> Dict[str, Any]:
        """ Manages the end-to-end design workflow. """
        print(f"Orchestrator: Starting design process for prompt: '{user_design_prompt}'")

        # 1. InputAgent: Get structured brief
        print("\nOrchestrator: Invoking InputAgent...")
        structured_brief = await self.input_agent.process(session, user_design_prompt)
        if "Error:" in structured_brief: # Basic error check
            return self._format_error("InputAgent failed", structured_brief)
        print(f"Orchestrator: InputAgent returned structured brief:\n{structured_brief}")
        session.add_message(Message(role="assistant", name=self.input_agent.config.name, content=structured_brief))

        # 2. DesignAgent: Generate DesignPlanModel
        print("\nOrchestrator: Invoking DesignAgent...")
        design_plan_or_error_str = await self.design_agent.generate_design_plan(session, structured_brief)

        if isinstance(design_plan_or_error_str, str) and "Error:" in design_plan_or_error_str:
            return self._format_error("DesignAgent failed to produce a valid plan", design_plan_or_error_str)
        if not isinstance(design_plan_or_error_str, DesignPlanModel):
             return self._format_error("DesignAgent returned unexpected type", str(design_plan_or_error_str))

        design_plan: DesignPlanModel = design_plan_or_error_str
        print(f"Orchestrator: DesignAgent returned DesignPlanModel:\n{design_plan.model_dump_json(indent=2)}")
        # DesignAgent already adds its (JSON) output to session history.

        # 3. RegulationsAgent: Check compliance (operates on the plan's textual description for now)
        # TODO: RegulationsAgent could be enhanced to understand DesignPlanModel directly.
        # For now, it will check the `plan_description` or a summary.
        print("\nOrchestrator: Invoking RegulationsAgent...")
        # Let's pass the plan_description for now, or a summary if available
        text_for_regulation_check = design_plan.plan_description + \
                                    f"\nContains {len(design_plan.walls)} walls and {len(design_plan.rooms)} rooms."

        compliance_result = await self.regulations_agent.check_compliance(session, text_for_regulation_check)
        if "Error:" in compliance_result:
            return self._format_error("RegulationsAgent failed", compliance_result)
        print(f"Orchestrator: RegulationsAgent returned compliance check:\n{compliance_result}")
        # RegulationsAgent adds its own message to session.

        final_result = {
            "status": "pending_revit_impl",
            "structured_brief": structured_brief,
            "design_plan": design_plan.model_dump(), # Store as dict
            "compliance_result": compliance_result,
            "revit_actions_summary": "Pending Revit implementation."
        }

        if "Design Approved" in compliance_result:
            print("\nOrchestrator: Design approved by RegulationsAgent.")
            revit_actions_log = await self.trigger_revit_implementation(session, design_plan)
            final_result["revit_actions_summary"] = revit_actions_log
            final_result["status"] = "completed" if "Error" not in revit_actions_log else "error_revit"
            print(f"Orchestrator: Revit implementation result: {revit_actions_log}")
        else:
            print("\nOrchestrator: Design requires modification or was not approved.")
            final_result["status"] = "requires_modification"

        print("\nOrchestrator: Design process finished.")
        return final_result

    def _format_error(self, message: str, details: str) -> Dict[str, Any]:
        print(f"Orchestrator: Error: {message}. Details: {details}")
        return {"status": "error", "message": message, "details": details}

    async def trigger_revit_implementation(self, session: Session, design_plan: DesignPlanModel) -> str:
        """ Translates DesignPlanModel to MCP tool calls and executes them. """
        print(f"Orchestrator: Attempting to trigger Revit implementation via MCP (Server: {FASTMCP_SERVER_URL}).")
        actions_taken = []
        errors_encountered = []

        try:
            self.mcp_toolset = MCPToolset(mcp_server_url=FASTMCP_SERVER_URL)
            await self.mcp_toolset.connect()
            available_tools = self.mcp_toolset.get_tool_names()
            print(f"Orchestrator: Connected to MCP Server. Available tools: {available_tools}")

            # Process Walls
            if "add_wall" in available_tools:
                for i, wall_data in enumerate(design_plan.walls):
                    call_args = {
                        "start_point": wall_data.start_point.to_list(),
                        "end_point": wall_data.end_point.to_list(),
                        "height": wall_data.height,
                        "level_name": wall_data.level_name
                    }
                    tool_call = Call(tool_name="add_wall", args=call_args)
                    tool_context = ToolContext(session=session, tool_call_id=f"wall_call_{i}")
                    print(f"Orchestrator: Calling add_wall with args: {call_args}")
                    try:
                        response: ToolResponse = await self.mcp_toolset.invoke_tool(tool_call, tool_context)
                        actions_taken.append(f"add_wall ({wall_data.wall_id or 'wall_'+str(i)}): {response.output}")
                    except Exception as e:
                        error_msg = f"Error calling add_wall for {wall_data.wall_id or 'wall_'+str(i)}: {e}"
                        print(error_msg)
                        errors_encountered.append(error_msg)
            else:
                actions_taken.append("MCP tool 'add_wall' not available on server.")

            # Process Rooms
            if "add_room" in available_tools:
                for i, room_data in enumerate(design_plan.rooms):
                    boundary_pts_xy = room_data.calculate_boundary_points_xy()
                    call_args = {
                        "room_name": room_data.name,
                        "boundary_points": boundary_pts_xy, # This is List[List[float]] for x,y
                        "level_name": room_data.level_name
                    }
                    tool_call = Call(tool_name="add_room", args=call_args)
                    tool_context = ToolContext(session=session, tool_call_id=f"room_call_{i}")
                    print(f"Orchestrator: Calling add_room with args: {call_args}")
                    try:
                        response: ToolResponse = await self.mcp_toolset.invoke_tool(tool_call, tool_context)
                        actions_taken.append(f"add_room ({room_data.room_id or room_data.name}): {response.output}")
                    except Exception as e:
                        error_msg = f"Error calling add_room for {room_data.room_id or room_data.name}: {e}"
                        print(error_msg)
                        errors_encountered.append(error_msg)
            else:
                actions_taken.append("MCP tool 'add_room' not available on server.")

        except ConnectionRefusedError:
            error_msg = f"Error: Could not connect to MCP Server at {FASTMCP_SERVER_URL}. Ensure server is running in Revit."
            print(error_msg)
            errors_encountered.append(error_msg)
            return error_msg # Return early as no actions can be taken
        except Exception as e:
            error_msg = f"Error during MCP interaction: {e}"
            print(error_msg)
            errors_encountered.append(error_msg)
        finally:
            if self.mcp_toolset and self.mcp_toolset.is_connected:
                await self.mcp_toolset.close()
                print("Orchestrator: MCPToolset connection closed.")

        summary = "Revit Actions Summary:\n" + "\n".join(actions_taken)
        if errors_encountered:
            summary += "\n\nErrors Encountered:\n" + "\n".join(errors_encountered)
            return f"Error: Some Revit actions failed. Summary: {summary}"

        return summary if actions_taken else "No specific Revit actions identified or taken."

    async def close(self):
        """Clean up resources, like closing MCPToolset connection if unexpectedly left open."""
        if self.mcp_toolset and self.mcp_toolset.is_connected:
            await self.mcp_toolset.close()
            print("Orchestrator: MCPToolset connection closed during agent shutdown.")


async def main():
    orchestrator = OrchestratorAgent()
    test_session = Session(session_id="test_orchestrator_pydantic_run")

    user_query = "Design a small rectangular cabin, about 5m wide and 6m long. It should have one main room called 'Living Quarters' and a smaller 2m x 2m room called 'Bathroom'. Use Level 1. Walls should be 3m high."

    final_output = await orchestrator.process_design_request(test_session, user_query)

    print("\n--- Orchestrator Final Output ---")
    # Pretty print the JSON parts if they exist
    if "design_plan" in final_output and isinstance(final_output["design_plan"], dict):
        final_output["design_plan"] = json.dumps(final_output["design_plan"], indent=2)

    for key, value in final_output.items():
        print(f"{key}: {value}")

    # print("\n--- Session History ---")
    # for msg_idx, msg in enumerate(test_session.history):
    #     content_summary = msg.content
    #     if isinstance(msg.content, str) and len(msg.content) > 150:
    #         try: # Try to parse if it's JSON from DesignAgent
    #             parsed_json = json.loads(msg.content)
    #             content_summary = f"JSON content (keys: {list(parsed_json.keys())})"
    #         except json.JSONDecodeError:
    #             content_summary = msg.content[:150] + "..."
    #     print(f"[{msg_idx}] [{msg.role} ({getattr(msg, 'name', 'N/A')})] {content_summary}")

    await orchestrator.close()

if __name__ == '__main__':
    # To run this:
    # 1. Ensure GOOGLE_API_KEY (or equivalent) is in .env or environment.
    # 2. Ensure FASTMCP_SERVER_URL is in .env or environment (or default is fine).
    # 3. Start the MCP Server in Revit.
    # 4. Run `python -m src.agents.orchestrator_agent` from the project root.
    # asyncio.run(main()) # Commented out for non-blocking tool execution
    pass
