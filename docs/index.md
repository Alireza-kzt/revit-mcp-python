# Welcome to the AI-Assisted Architectural Design System

This project implements an AI-assisted architectural design system that integrates with Autodesk Revit. It leverages Google's Agent Development Kit (ADK-Python v1.0) and the Model Context Protocol (MCP) to facilitate communication between specialized AI agents and a Revit backend.

## Project Goal

The primary goal is to create a proof-of-concept system where a user can provide a design brief, and a series of AI agents will process this brief, generate a conceptual design, check it against simplified regulations, and then (conceptually) instruct Revit to model the approved design.

This system demonstrates:
- Multi-agent collaboration using ADK.
- Integration with a 3D modeling environment (Revit) via MCP.
- A modular approach to building AI-powered design tools.

## Key Technologies

*   **Google Agent Development Kit (ADK-Python v1.0):** Used for defining and orchestrating the AI agents.
*   **FastMCP 2.x:** Used to create the MCP server within Revit, exposing Revit API functionalities as tools.
*   **PyRevit:** A Python scripting environment for Revit, used to host the FastMCP server and provide a user interface within Revit.
*   **Autodesk Revit:** The target BIM platform for architectural modeling.
*   **MkDocs:** For generating this documentation.
*   **pytest:** For unit testing components of the system.

## Navigation

Use the navigation bar to explore different aspects of the system:
*   **System Overview:** High-level architecture and workflow.
*   **Agents:** Detailed descriptions of each AI agent.
*   **Revit Integration:** Information on the PyRevit plugin and MCP server.
*   **Usage Guide:** Instructions on how to set up and run the system.
*   **Development:** Notes for developers, including testing and CI.

We hope this documentation provides a clear understanding of the project's structure and functionality.
