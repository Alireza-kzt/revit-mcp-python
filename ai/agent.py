"""Entry point for ADK loading."""

from google.adk.agents import LoopAgent
from ai.agents.orchestrator_agent import OrchestratorAgent

root_agent = LoopAgent(
    name="MainAgent",
    sub_agents=[OrchestratorAgent()],
)
