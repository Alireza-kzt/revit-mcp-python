# coding: utf-8
"""
PyRevit Script for AI Design Assistant Server Control

This script provides functionality to start and stop the FastMCP server
that exposes Revit functionalities to AI agents.
"""

__title__ = "AI Design Server"
__author__ = "AI Design Team (Jules)"
__doc__ = """
Click to start or stop the AI Design MCP Server.
The server allows AI agents to interact with the current Revit model.
Ensure 'AI_DESIGN_ASSISTANT_PATH' environment variable is set to the
root directory of the AI Design Assistant project for module discovery.
"""

import sys
import os
import asyncio
import threading
import logging
from typing import Optional, Any

# --- Revit API Imports ---
# Attempt to import Revit API modules. This will only work inside Revit.
try:
    import clr
    clr.AddReference("RevitAPI")
    clr.AddReference("RevitAPIUI")
    from Autodesk.Revit.DB import Document # Transaction not directly used here
    from Autodesk.Revit.UI import UIApplication, TaskDialog, TaskDialogCommonButtons, TaskDialogResult
    REVIT_ENVIRONMENT = True
except ImportError:
    REVIT_ENVIRONMENT = False
    # Mock objects for standalone testing or type hinting
    class MockUIApplication:
        def __init__(self): self.ActiveUIDocument = MockUIDocument()
        @property
        def Application(self): return MockApplication() # For context setting
    class MockApplication: pass # Placeholder for Application object
    class MockUIDocument:
        def __init__(self): self.Document = MockDocument()
    class MockDocument:
        def __init__(self): self.Title = "Mock Revit Document"
    class MockTaskDialog:
        @staticmethod
        def Show(title: str, message: str) -> None: print(f"TaskDialog (Mock): {title} - {message}")
    class MockTaskDialogCommonButtons: Cancel=1; Ok=2 # Simplified
    class MockTaskDialogResult: Cancel=1; Ok=2 # Simplified

    UIApplication = MockUIApplication
    TaskDialog = MockTaskDialog
    TaskDialogCommonButtons = MockTaskDialogCommonButtons
    TaskDialogResult = MockTaskDialogResult
    Document = MockDocument # So type hint for doc works

# --- Server State & Configuration ---
SERVER_THREAD: Optional[threading.Thread] = None
SERVER_RUNNING: bool = False
MCP_SERVER_MODULE: Optional[Any] = None # To hold the imported mcp_server module
SERVER_HOST: str = os.getenv("FASTMCP_SERVER_HOST", "127.0.0.1") # Allow override via env
SERVER_PORT: int = int(os.getenv("FASTMCP_SERVER_PORT", "8765")) # Allow override via env

# --- Logging Setup ---
# Configure a logger for this script. Output can be seen in PyRevit's log/output window.
LOG_LEVEL = logging.INFO # logging.DEBUG for more verbosity
script_logger = logging.getLogger("AIDesignServer")
if not script_logger.handlers: # Avoid adding multiple handlers on script reload
    # Basic configuration for PyRevit's output or a file
    # handler = logging.StreamHandler(sys.stdout) # For console output
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # handler.setFormatter(formatter)
    # script_logger.addHandler(handler)
    # For production, PyRevit might have its own logging setup.
    # For now, let's keep it simple; print statements and TaskDialogs provide feedback.
    # If more detailed logging is needed, one might log to a file:
    # log_file_path = os.path.join(os.getenv("TEMP", "/tmp"), "pyrevit_ai_design_server.log")
    # file_handler = logging.FileHandler(log_file_path)
    # file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    # script_logger.addHandler(file_handler)
    pass # Rely on print and TaskDialog for now for simplicity in PyRevit button context
script_logger.setLevel(LOG_LEVEL)


def _show_dialog(title: str, message: str, is_error: bool = False) -> None:
    """Helper to show TaskDialog or print if not in Revit."""
    script_logger.info(f"Dialog: {title} - {message}")
    if REVIT_ENVIRONMENT:
        TaskDialog.Show(title, message)
    else:
        print(f"{'ERROR' if is_error else 'INFO'}: [{title}] {message}")

def ensure_project_path_and_import_server() -> bool:
    """
    Ensures project's 'src' directory is in sys.path and imports mcp_server.
    Relies on 'AI_DESIGN_ASSISTANT_PATH' environment variable.
    Returns True if successful, False otherwise.
    """
    global MCP_SERVER_MODULE
    if MCP_SERVER_MODULE: return True # Already imported

    project_root = os.getenv("AI_DESIGN_ASSISTANT_PATH")
    if not project_root:
        msg = ("Environment variable 'AI_DESIGN_ASSISTANT_PATH' is not set. "
               "This is required to locate the AI design server module. "
               "Please set it to the root directory of the AI Design Assistant project.")
        _show_dialog("AI Server Error", msg, is_error=True)
        script_logger.error(msg)
        return False

    src_path = os.path.join(project_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        script_logger.info(f"Added '{src_path}' to sys.path for module import.")

    try:
        from revit_server import mcp_server # Assuming mcp_server.py is in src/revit_server/
        MCP_SERVER_MODULE = mcp_server
        script_logger.info("Successfully imported 'revit_server.mcp_server' module.")
        return True
    except ImportError as e:
        msg = (f"Failed to import 'mcp_server' module from '{src_path}'. Error: {e}. "
               "Ensure the project structure is correct and 'AI_DESIGN_ASSISTANT_PATH' points to the project root.")
        _show_dialog("AI Server Error", msg, is_error=True)
        script_logger.error(msg, exc_info=True)
        return False
    except Exception as e: # Catch any other unexpected error during import
        msg = f"An unexpected error occurred during server module import: {e}"
        _show_dialog("AI Server Error", msg, is_error=True)
        script_logger.error(msg, exc_info=True)
        return False

def start_mcp_server_thread(uiapp: Any) -> None:
    """Starts the FastMCP server in a separate thread."""
    global SERVER_THREAD, SERVER_RUNNING, MCP_SERVER_MODULE

    if SERVER_RUNNING:
        _show_dialog("AI Server", "Server is already running.")
        return

    if not ensure_project_path_and_import_server():
        return # Module import or path setup failed

    # Get Revit context if available
    doc_title = "N/A (Not in Revit or no active document)"
    if REVIT_ENVIRONMENT:
        if not uiapp or not uiapp.ActiveUIDocument:
            _show_dialog("AI Server Error", "No active Revit document found. Please open a project.", is_error=True)
            return
        uidoc = uiapp.ActiveUIDocument
        doc = uidoc.Document
        # Pass the actual Revit Application object, not uiapp itself for Application
        MCP_SERVER_MODULE.set_revit_context(uiapp.Application, uidoc, doc)
        doc_title = doc.Title
        script_logger.info(f"Revit context set for document: {doc_title}")
    else:
        # For testing outside Revit, pass mock or None context
        mock_app, mock_uidoc, mock_doc = (UIApplication().Application, UIApplication().ActiveUIDocument, UIApplication().ActiveUIDocument.Document)
        MCP_SERVER_MODULE.set_revit_context(mock_app, mock_uidoc, mock_doc)
        doc_title = mock_doc.Title
        script_logger.info("Running outside Revit; mock context passed to server.")

    def server_runner():
        global SERVER_RUNNING
        SERVER_RUNNING = True
        script_logger.info(f"MCP server thread started. Attempting to run server on {SERVER_HOST}:{SERVER_PORT}.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # MCP_SERVER_MODULE.run_server is an async function
            loop.run_until_complete(MCP_SERVER_MODULE.run_server(host=SERVER_HOST, port=SERVER_PORT))
        except SystemExit: # Can be raised by uvicorn on shutdown signals
            script_logger.info("Server SystemExit caught, likely normal shutdown.")
        except ConnectionRefusedError: # Specific error for port binding issues
             _show_dialog("AI Server Error", f"Connection refused. Port {SERVER_PORT} might be in use or blocked.", is_error=True)
             script_logger.error(f"Connection refused on port {SERVER_PORT}.", exc_info=True)
        except OSError as ose: # Catch other OS errors like port already in use
            if "address already in use" in str(ose).lower():
                 _show_dialog("AI Server Error", f"Address {SERVER_HOST}:{SERVER_PORT} already in use. Is another server running?", is_error=True)
                 script_logger.error(f"Address {SERVER_HOST}:{SERVER_PORT} already in use.", exc_info=True)
            else:
                 _show_dialog("AI Server Error", f"Server OS error: {ose}", is_error=True)
                 script_logger.error(f"Server OS error: {ose}", exc_info=True)
        except Exception as e: # Catch-all for other errors during server run
            _show_dialog("AI Server Error", f"Server failed to start or crashed: {e}", is_error=True)
            script_logger.error(f"Error running MCP server: {e}", exc_info=True)
        finally:
            SERVER_RUNNING = False
            if loop and not loop.is_closed():
                loop.close()
            script_logger.info("MCP server thread finished and loop closed.")
            # Update button state or notify user that server has stopped.
            # This runs in the thread, so UI updates need care (e.g. via pyrevit forms execute_async)

    SERVER_THREAD = threading.Thread(target=server_runner, daemon=True)
    SERVER_THREAD.start()

    # Check status after a short delay - this is tricky because server starts async
    # A better approach is if the server itself signals its readiness (e.g. via a queue or event)
    # For now, a timed check with user feedback.
    def _check_startup():
        if SERVER_RUNNING:
            _show_dialog("AI Server", f"AI Design MCP Server started on http://{SERVER_HOST}:{SERVER_PORT}\nActive Document: {doc_title}")
        else:
            # Error message would have been shown by the thread if startup failed quickly.
            # This case handles if thread exited without setting SERVER_RUNNING or very fast failure.
            _show_dialog("AI Server Warning", "Server may not have started correctly. Check logs if issues persist.", is_error=True)

    threading.Timer(2.0, _check_startup).start() # Increased delay

def stop_mcp_server_thread() -> None:
    """Attempts to signal the MCP server to stop."""
    global SERVER_RUNNING, SERVER_THREAD

    if not SERVER_RUNNING:
        _show_dialog("AI Server", "Server is not currently running.")
        return

    script_logger.info("Attempting to stop MCP server...")
    # Graceful shutdown of an asyncio server from another thread is complex.
    # Uvicorn, used by FastMCP, listens for SIGINT/SIGTERM.
    # We can't easily send these signals to a thread in Python.
    # The `mcp_server.run_async` itself doesn't expose a direct shutdown handle.
    # A common pattern is to have the server's async loop periodically check a flag.
    # For now, setting SERVER_RUNNING = False is an optimistic signal.
    # The server thread is a daemon, so it will exit when Revit exits.

    # TODO: Implement a more robust shutdown mechanism if possible.
    # For example, mcp_server could have a global `shutdown_event = asyncio.Event()`
    # and the server loop would `await asyncio.wait_for(shutdown_event.wait(), timeout=1)`
    # Then, this function could `loop.call_soon_threadsafe(shutdown_event.set)` on the server's loop.
    # This requires access to the server's event loop from here.

    SERVER_RUNNING = False # Signal the server loop (if it were designed to check this)
    # SERVER_THREAD = None # Don't clear thread, it might be cleaning up.

    msg = ("Server stop requested. Note: Graceful shutdown for the embedded server is "
           "currently conceptual. The server process might continue until Revit exits or "
           "the port is freed. If issues persist, restarting Revit might be necessary.")
    _show_dialog("AI Server", msg)
    script_logger.warning(msg)


# --- Main Execution (when PyRevit button is clicked) ---
if __name__ == "__main__":
    current_uiapp: Optional[UIApplication] = None
    if REVIT_ENVIRONMENT:
        # `__revit__` is the global UIApplication instance provided by PyRevit
        current_uiapp = __revit__
    else:
        # Standalone testing mode (e.g., `python script.py`)
        logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
        script_logger.info("Running PyRevit script in standalone test mode (outside Revit).")
        current_uiapp = UIApplication() # Mock instance for testing
        # For standalone, try to guess project root if AI_DESIGN_ASSISTANT_PATH not set
        if not os.getenv("AI_DESIGN_ASSISTANT_PATH"):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root_guess = os.path.abspath(os.path.join(script_dir, "../../../../")) # Adjust depth as needed
            os.environ["AI_DESIGN_ASSISTANT_PATH"] = project_root_guess
            script_logger.info(f"Guessed project root for testing: {project_root_guess}")

    if not current_uiapp:
        _show_dialog("AI Server Error", "Failed to get Revit application context.", is_error=True)
    elif SERVER_RUNNING:
        stop_mcp_server_thread()
    else:
        if SERVER_THREAD and SERVER_THREAD.is_alive():
            _show_dialog("AI Server Warning", "Server thread is still alive but reported as not running. Please wait or try stopping again.")
        else:
            start_mcp_server_thread(current_uiapp)

elif REVIT_ENVIRONMENT:
    # This block could be used if the script is loaded by PyRevit but not run via click
    # (e.g., on Revit startup if this script were part of a startup sequence).
    # For a button, this part is less critical.
    # script_logger.debug("AI Design Server script loaded by PyRevit.")
    pass
