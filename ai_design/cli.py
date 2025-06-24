import os
from .agents.orchestrator_agent import OrchestratorAgent


def main() -> None:
    mcp_url = os.environ.get("FASTMCP_SERVER_URL", "http://localhost:8000")
    orchestrator = OrchestratorAgent(mcp_url)
    print("Orchestrator initialized with MCP url", mcp_url)


if __name__ == "__main__":
    main()
