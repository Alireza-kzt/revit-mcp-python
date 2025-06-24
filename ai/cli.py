import os
from .agents.orchestrator_agent import OrchestratorAgent


def main() -> None:
    OrchestratorAgent()
    print("Orchestrator initialized.")


if __name__ == "__main__":
    main()
