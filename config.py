import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# General configuration variables for the project

# Directory containing the revit MCP python package
REVIT_MCP_PY_DIR: str = os.getenv("REVIT_MCP_PY_DIR", "./revit-mcp-python")

# Revit connection information
REVIT_HOST: str = os.getenv("REVIT_HOST", "localhost")
REVIT_PORT: int = int(os.getenv("REVIT_PORT", 48884))

# Base URL for Revit MCP API
BASE_URL: str = os.getenv(
    "BASE_URL",
    f"http://{REVIT_HOST}:{REVIT_PORT}/revit_mcp",
)
