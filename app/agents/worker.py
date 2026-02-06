# agents/worker.py
import json
import logging
from pathlib import Path

logger = logging.getLogger("chimera.worker")

class Worker:
    def __init__(self, tasks_file: str = "tasks.json"):
        """
        Initialize the Worker with a tasks file path.
        
        Args:
            tasks_file: Path to the JSON file where tasks will be stored
        """
        self.tasks_file = tasks_file
    
    async def save_tasks_to_file(self, plan_data: dict) -> str:
        """
        Save the serialized plan data (tasks) to a JSON file.
        This is the Worker's responsibility for persisting the Planner's output.
        
        Args:
            plan_data: The task data from the planner (dict or list)
        
        Returns:
            Success message with file path
        """
        try:
            # Ensure the plan_data is in a consistent format
            if isinstance(plan_data, dict):
                # If it's a dict, wrap it in a list or use as-is depending on structure
                if "tasks" in plan_data:
                    tasks_to_save = plan_data
                else:
                    # Single task, wrap in tasks array
                    tasks_to_save = {"tasks": [plan_data]}
            elif isinstance(plan_data, list):
                # Already a list of tasks
                tasks_to_save = {"tasks": plan_data}
            else:
                logger.error(f"Invalid plan_data type: {type(plan_data)}")
                return f"Error: Invalid plan data type"
            
            # Write to file
            file_path = Path(self.tasks_file)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tasks_to_save, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Tasks saved to {file_path.absolute()}")
            return f"Tasks successfully saved to {file_path.absolute()}"
        
        except Exception as e:
            logger.exception(f"Failed to save tasks to file: {e}")
            return f"Error saving tasks: {str(e)}"
    
    async def execute_task(self, task_id: str):
        """
        Execute a specific task by its ID.
        Loads tasks from the JSON file, updates status, and saves back.
        """
        try:
            # 1. Load the structured task list
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            tasks = data.get("tasks", [])
            
            # 2. Find and 'Execute' the specific task logic
            # For 'Social Lunch', the worker might call a Calendar Tool
            logger.info(f"WORKER ACTING: Executing task {task_id}...")
            
            task_found = False
            # 3. Update the state (Persistence)
            for t in tasks:
                if t.get("id") == task_id:
                    t["status"] = "completed"
                    task_found = True
                    logger.info(f"Task {task_id} marked as completed")
                    break
            
            if not task_found:
                logger.warning(f"Task {task_id} not found in tasks file")
                return f"Task {task_id} not found"
            
            # 4. Save back to the 'Shared Memory'
            data["tasks"] = tasks
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            return f"Task {task_id} completed successfully"
        
        except FileNotFoundError:
            logger.error(f"Tasks file {self.tasks_file} not found")
            return f"Tasks file not found: {self.tasks_file}"
        except Exception as e:
            logger.exception(f"Error executing task: {e}")
            return f"Error executing task: {str(e)}"