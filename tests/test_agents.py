import pytest
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Conditional import for dotenv
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
except ImportError:
    pass # python-dotenv not installed

from adk.llm_service_adapter import LlmServiceAdapter
from adk.message import AssistantMessage, ToolResponse, Call, ToolContext
from adk.session import Session
from adk.mcp_toolset import MCPToolset

# Import Agents and Models
from src.agents.input_agent import InputAgent
from src.agents.design_agent import DesignAgent
from src.agents.regulations_agent import RegulationsAgent
from src.agents.orchestrator_agent import OrchestratorAgent
from src.shared_models import DesignPlanModel, WallModel, RoomModel, PointModel


# --- Fixtures ---

@pytest.fixture
def test_session() -> Session:
    return Session(session_id="test_session_pydantic")

@pytest.fixture
def mocked_llm_adapter() -> AsyncMock:
    adapter = AsyncMock(spec=LlmServiceAdapter)
    adapter.invoke_llm = AsyncMock()
    return adapter

@pytest.fixture
def input_agent_mocked(mocked_llm_adapter: AsyncMock) -> InputAgent:
    return InputAgent(llm_service_adapter=mocked_llm_adapter)

@pytest.fixture
def design_agent_mocked(mocked_llm_adapter: AsyncMock) -> DesignAgent:
    return DesignAgent(llm_service_adapter=mocked_llm_adapter)

@pytest.fixture
def regulations_agent_mocked(mocked_llm_adapter: AsyncMock) -> RegulationsAgent:
    return RegulationsAgent(llm_service_adapter=mocked_llm_adapter)

@pytest.fixture
def orchestrator_agent_mocked(
    input_agent_mocked: InputAgent,
    design_agent_mocked: DesignAgent,
    regulations_agent_mocked: RegulationsAgent
) -> OrchestratorAgent:
    with patch('src.agents.orchestrator_agent.InputAgent', return_value=input_agent_mocked), \
         patch('src.agents.orchestrator_agent.DesignAgent', return_value=design_agent_mocked), \
         patch('src.agents.orchestrator_agent.RegulationsAgent', return_value=regulations_agent_mocked):
        orchestrator = OrchestratorAgent()
    return orchestrator

# --- Agent Tests ---

@pytest.mark.asyncio
async def test_input_agent_process(input_agent_mocked: InputAgent, test_session: Session):
    user_prompt = "I want a modern house."
    expected_brief = "Structured Brief:\n- Style: Modern"
    input_agent_mocked.llm_service_adapter.invoke_llm.return_value = AssistantMessage(content=expected_brief)

    result = await input_agent_mocked.process(test_session, user_prompt)

    assert expected_brief in result
    input_agent_mocked.llm_service_adapter.invoke_llm.assert_called_once()
    messages_passed = input_agent_mocked.llm_service_adapter.invoke_llm.call_args[0][0]
    assert user_prompt in messages_passed[0].content

@pytest.mark.asyncio
async def test_design_agent_generates_valid_design_plan_model(design_agent_mocked: DesignAgent, test_session: Session):
    structured_brief = "Design a small cabin with one room."
    mock_plan_dict = {
        "plan_description": "A simple one-room cabin.",
        "walls": [{
            "start_point": {"x": 0, "y": 0, "z": 0}, "end_point": {"x": 5, "y": 0, "z": 0},
            "height": 3.0, "level_name": "Level 1", "wall_id": "wall_south"
        }],
        "rooms": [{
            "name": "Main Cabin Room", "level_name": "Level 1",
            "center_x": 2.5, "center_y": 2.0, "width": 4.8, "length": 3.8, "room_id": "main_room"
        }]
    }
    mock_json_output = json.dumps(mock_plan_dict)
    # DesignAgent's 'invoke' method calls llm_service_adapter.invoke_llm.
    # So we mock what invoke_llm returns.
    design_agent_mocked.llm_service_adapter.invoke_llm.return_value = AssistantMessage(content=mock_json_output)

    # Call the method that uses the mocked LLM call
    result = await design_agent_mocked.generate_design_plan(test_session, structured_brief)

    assert isinstance(result, DesignPlanModel)
    assert result.plan_description == mock_plan_dict["plan_description"]
    assert len(result.walls) == 1
    assert result.walls[0].wall_id == "wall_south"
    assert result.rooms[0].name == "Main Cabin Room"

    design_agent_mocked.llm_service_adapter.invoke_llm.assert_called_once()
    messages_passed = design_agent_mocked.llm_service_adapter.invoke_llm.call_args[0][0]
    prompt_content = messages_passed[0].content # LlmAgent's invoke passes messages to adapter
    assert DesignPlanModel.schema_json(indent=2) in prompt_content

    agent_state = test_session.get_agent_state(design_agent_mocked.config.name)
    assert agent_state is not None
    assert agent_state.get("design_plan_model") == result.model_dump()


@pytest.mark.asyncio
async def test_design_agent_handles_invalid_json_output(design_agent_mocked: DesignAgent, test_session: Session):
    structured_brief = "Design something complex."
    invalid_json = "This is not valid JSON { definitely not"
    design_agent_mocked.llm_service_adapter.invoke_llm.return_value = AssistantMessage(content=invalid_json)

    result = await design_agent_mocked.generate_design_plan(test_session, structured_brief)

    assert isinstance(result, str)
    assert "Error: LLM output was not valid DesignPlanModel JSON" in result
    agent_state = test_session.get_agent_state(design_agent_mocked.config.name)
    assert "design_plan_error" in agent_state
    assert agent_state["raw_output"] == invalid_json

@pytest.mark.asyncio
async def test_regulations_agent_check_compliance_with_plan_description(regulations_agent_mocked: RegulationsAgent, test_session: Session):
    design_plan_summary_for_regulations = "Conceptual plan for a small cabin. Contains 1 walls and 1 rooms."
    expected_compliance_result = "Design Approved"
    regulations_agent_mocked.llm_service_adapter.invoke_llm.return_value = AssistantMessage(content=expected_compliance_result)

    result = await regulations_agent_mocked.check_compliance(test_session, design_plan_summary_for_regulations)

    assert expected_compliance_result in result
    messages_passed = regulations_agent_mocked.llm_service_adapter.invoke_llm.call_args[0][0]
    assert design_plan_summary_for_regulations in messages_passed[0].content

# --- OrchestratorAgent Tests (Now with Pydantic and real MCPToolset mock) ---

@patch('src.agents.orchestrator_agent.MCPToolset')
@pytest.mark.asyncio
async def test_orchestrator_agent_workflow_approved_pydantic_mcp(
    MockMCPToolsetType: MagicMock,
    orchestrator_agent_mocked: OrchestratorAgent,
    input_agent_mocked: InputAgent,
    design_agent_mocked: DesignAgent,
    regulations_agent_mocked: RegulationsAgent,
    test_session: Session
):
    user_prompt = "Build a compliant modern house with one wall and one room."
    mock_brief = "Structured Brief: Modern, compliant, one wall, one room."

    mock_design_plan = DesignPlanModel(
        plan_description="A fantastic modern, compliant house.",
        walls=[WallModel(start_point=PointModel(x=0,y=0,z=0), end_point=PointModel(x=5,y=0,z=0), height=3.0, level_name="L1", wall_id="w_south")],
        rooms=[RoomModel(name="LivingRoom", level_name="L1", center_x=2.5, center_y=2.0, width=4.0, length=3.0, room_id="r_living")]
    )
    mock_compliance_approved = "Design Approved"

    input_agent_mocked.process = AsyncMock(return_value=mock_brief)
    design_agent_mocked.generate_design_plan = AsyncMock(return_value=mock_design_plan)
    regulations_agent_mocked.check_compliance = AsyncMock(return_value=mock_compliance_approved)

    mock_mcp_instance = AsyncMock(spec=MCPToolset)
    mock_mcp_instance.connect = AsyncMock()
    mock_mcp_instance.close = AsyncMock()
    mock_mcp_instance.get_tool_names = MagicMock(return_value=["add_wall", "add_room"])
    successful_tool_response = ToolResponse(output='{"status":"success"}', call=MagicMock(), tool_context=MagicMock())
    mock_mcp_instance.invoke_tool = AsyncMock(return_value=successful_tool_response)

    MockMCPToolsetType.return_value = mock_mcp_instance

    with patch.dict(os.environ, {"FASTMCP_SERVER_URL": "http://fake-mcp-server:8000"}):
        result = await orchestrator_agent_mocked.process_design_request(test_session, user_prompt)

    input_agent_mocked.process.assert_called_once_with(test_session, user_prompt)
    design_agent_mocked.generate_design_plan.assert_called_once_with(test_session, mock_brief)
    expected_text_for_regulations = mock_design_plan.plan_description + \
                                   f"\nContains {len(mock_design_plan.walls)} walls and {len(mock_design_plan.rooms)} rooms."
    regulations_agent_mocked.check_compliance.assert_called_once_with(test_session, expected_text_for_regulations)

    MockMCPToolsetType.assert_called_once_with(mcp_server_url="http://fake-mcp-server:8000")
    mock_mcp_instance.connect.assert_called_once()

    assert mock_mcp_instance.invoke_tool.call_count == 2

    expected_wall_args = {
        "start_point": [0.0, 0.0, 0.0], "end_point": [5.0, 0.0, 0.0],
        "height": 3.0, "level_name": "L1"
    }
    room = mock_design_plan.rooms[0]
    expected_room_boundary = room.calculate_boundary_points_xy()
    expected_room_args = {
        "room_name": "LivingRoom",
        "boundary_points": expected_room_boundary,
        "level_name": "L1"
    }

    found_wall_call = False
    found_room_call = False
    for call_obj_tuple in mock_mcp_instance.invoke_tool.call_args_list:
        call_obj: Call = call_obj_tuple[0][0]
        if call_obj.tool_name == "add_wall" and call_obj.args == expected_wall_args:
            found_wall_call = True
        if call_obj.tool_name == "add_room" and call_obj.args == expected_room_args:
            found_room_call = True

    assert found_wall_call, "add_wall tool call not found with expected arguments"
    assert found_room_call, "add_room tool call not found with expected arguments"

    mock_mcp_instance.close.assert_called_once()

    assert result["status"] == "completed"
    assert result["design_plan"] == mock_design_plan.model_dump()
    assert "add_wall (w_south):" in result["revit_actions_summary"]
    assert "add_room (r_living):" in result["revit_actions_summary"]


@patch('src.agents.orchestrator_agent.MCPToolset')
@pytest.mark.asyncio
async def test_orchestrator_agent_workflow_needs_modification_pydantic(
    MockMCPToolsetType: MagicMock,
    orchestrator_agent_mocked: OrchestratorAgent,
    input_agent_mocked: InputAgent,
    design_agent_mocked: DesignAgent,
    regulations_agent_mocked: RegulationsAgent,
    test_session: Session
):
    user_prompt = "Build a non-compliant house."
    mock_brief = "Structured Brief: Non-compliant."
    mock_design_plan = DesignPlanModel(plan_description="A non-compliant house that's too small.")
    mock_compliance_modified = "Design Requires Modification: Overall size too small."

    input_agent_mocked.process = AsyncMock(return_value=mock_brief)
    design_agent_mocked.generate_design_plan = AsyncMock(return_value=mock_design_plan)
    regulations_agent_mocked.check_compliance = AsyncMock(return_value=mock_compliance_modified)

    mock_mcp_instance = MockMCPToolsetType.return_value

    result = await orchestrator_agent_mocked.process_design_request(test_session, user_prompt)

    mock_mcp_instance.connect.assert_not_called()
    assert result["status"] == "requires_modification"
    assert result["compliance_result"] == mock_compliance_modified
    assert result["design_plan"] == mock_design_plan.model_dump()

def test_placeholder():
    assert True
