from pyrevit import forms
import threading
from ai_design import mcp_server

if forms.alert("Start AI Design MCP server?", yes=True, no=True) == forms.AlertResult.yes:
    threading.Thread(target=mcp_server.run, daemon=True).start()
    forms.alert("AI Design Server started", exitscript=True)
