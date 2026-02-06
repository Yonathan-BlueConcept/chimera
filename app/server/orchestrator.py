import json
import os
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from agents.planner import Planner
from agents.worker import Worker
from agents.judge import Judge
from models.model import UserInput

# 1. Initialize FastMCP (The recommended base class for Chimera)
# This provides the @tool decorator and handles Stdio transport automatically.
server = FastMCP("chimera-orchestrator")

# Configure a module logger (writes to stderr by default)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chimera.orchestrator")

# Determine the project root directory (2 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
TASKS_FILE_PATH = PROJECT_ROOT / "tasks.json"

# Log the tasks file location for visibility
logger.info(f"Tasks will be stored at: {TASKS_FILE_PATH.absolute()}")

# 2. Initialize the Planner (The Strategist)
# Following Section 3.1.1: The Planner decomposes high-level goals.
planner = Planner()

# 3. Initialize the Worker (The Executor)
# The Worker is responsible for persisting tasks and executing them
# the worker put tasks in to json file
worker = Worker(tasks_file=str(TASKS_FILE_PATH))

# 4. Initialize the Judge (The Validator)
# The Judge validates task completion and triggers replanning if needed
judge = Judge(tasks_file=str(TASKS_FILE_PATH), max_retries=3)

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

        # 4. Pass the plan data to the Worker for persistence
        # Instead of returning the data, save it to a JSON file
        logger.info("Passing plan data to Worker for persistence...")
        save_result = await worker.save_tasks_to_file(plan_data)
        
        # Log the save result
        logger.info("Worker save result: %s", save_result)
        
        # Return a response that includes both the save status and the plan preview
        try:
            if isinstance(plan_data, (dict, list)):
                plan_preview = json.dumps(plan_data, ensure_ascii=False, indent=2)
            else:
                plan_preview = str(plan_data)
            
            response = {
                "status": "success",
                "message": save_result,
                "plan_preview": plan_preview
            }
            
            return json.dumps(response, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.exception("Failed to format response")
            return json.dumps({
                "status": "error",
                "message": f"Failed to format response: {e}",
                "save_result": save_result
            })

    except Exception as e:
        return f"Orchestration Error: {str(e)}"

@server.tool()
async def validate_and_replan(original_message: str) -> str:
    """
    Validate if the worker completed all tasks. If not, trigger replanning.
    
    This tool uses the Judge to check task completion status and automatically
    re-run the planner if tasks are incomplete or failed.
    
    Args:
        original_message: The original user request that generated the tasks
    
    Returns:
        JSON string with validation results and replanning status
    """
    logger.info("Validate and replan triggered")
    
    # Create UserInput from the original message
    user_input = UserInput(
        session_id="session-validation-001",
        message=original_message,
        document_text=""
    )
    
    try:
        # Trigger the judge to validate and replan if needed
        judgment = await judge.judge_and_replan(planner, user_input, worker)
        
        # Format the response
        return json.dumps(judgment, ensure_ascii=False, indent=2)
    
    except Exception as e:
        logger.exception("Error in validate_and_replan")
        return json.dumps({
            "status": "error",
            "message": f"Validation error: {str(e)}"
        })

@server.tool()
async def check_task_status() -> str:
    """
    Check the current status of all tasks without triggering replanning.
    
    Returns:
        JSON string with task completion statistics
    """
    logger.info("Check task status triggered")
    
    try:
        validation = await judge.validate_task_completion()
        return json.dumps(validation, ensure_ascii=False, indent=2)
    
    except Exception as e:
        logger.exception("Error checking task status")
        return json.dumps({
            "status": "error",
            "message": f"Status check error: {str(e)}"
        })


if __name__ == "__main__":
    # In FastMCP, .run() defaults to stdio transport, which is required
    # for local MCP connectivity to the VS Code Chat system.
    server.run()