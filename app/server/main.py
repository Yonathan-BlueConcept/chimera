import json
import os
import logging
from mcp.server.fastmcp import FastMCP
from agents.planner import Planner
from models.model import UserInput

# 1. Initialize FastMCP (The recommended base class for Chimera)
# This provides the @tool decorator and handles Stdio transport automatically.
server = FastMCP("chimera-orchestrator")

# Configure a module logger (writes to stderr by default)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chimera.orchestrator")

# 2. Initialize the Planner (The Strategist)
# Following Section 3.1.1: The Planner decomposes high-level goals.
planner = Planner()

@server.tool()
async def chat(message, document: str | None = None) -> str:
    """
    Chimera Orchestrator Tool: Decodes user intent and triggers the
    FastRender Planner to generate a task DAG.
    """

    # Normalize incoming message which may be a plain string or an object/dict
    if isinstance(message, str):
        text = message
    elif isinstance(message, dict):
        # common fields that may carry text
        text = message.get("message") or message.get("text") or json.dumps(message)
    else:
        # fallback to string representation
        try:
            text = str(message)
        except Exception:
            text = ""

    # Optional: Log for visibility as the Orchestrator Hub (stderr)
    logger.info("Orchestrator received: %s", text)

    # Map input to the UserInput model for consistent schema management
    user_input = UserInput(
        session_id="session-init-001",
        message=text,
        document_text=document if document else ""
    )

    try:
        # 3. Trigger the Planner (The Reasoning Head)
        plan_data = await planner.create_plan(user_input)

        # Normalize planner output to a JSON string for the MCP transport
        try:
            # plan_data is now a dict/list/string from planner
            if isinstance(plan_data, (dict, list)):
                serialized = json.dumps(plan_data, ensure_ascii=False)
            else:
                serialized = str(plan_data)

            # Log the serialized planner output to stderr (does not interfere with MCP stdio)
            logger.info("Planner output serialized: %s", serialized)
            return serialized
        except Exception as e:
            logger.exception("Failed to serialize planner output")
            return f"Orchestration Error: failed to serialize planner output: {e}"

    except Exception as e:
        return f"Orchestration Error: {str(e)}"

if __name__ == "__main__":
    # In FastMCP, .run() defaults to stdio transport, which is required
    # for local MCP connectivity to the VS Code Chat system.
    server.run()