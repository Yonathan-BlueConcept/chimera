# agents/judge.py
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from models.model import UserInput

logger = logging.getLogger("chimera.judge")


class Judge:
    """
    The Judge validates task execution and decides whether to re-plan.
    
    Responsibilities:
    - Verify worker task completion
    - Check task quality/success
    - Trigger replanning if tasks are incomplete or failed
    - Manage retry logic
    """
    
    def __init__(self, tasks_file: str = "tasks.json", max_retries: int = 3):
        """
        Initialize the Judge with validation parameters.
        
        Args:
            tasks_file: Path to the JSON file containing tasks
            max_retries: Maximum number of times to retry failed tasks
        """
        self.tasks_file = tasks_file
        self.max_retries = max_retries
    
    async def validate_task_completion(self) -> Dict:
        """
        Check if all tasks in the tasks file have been completed.
        
        Returns:
            Dict with validation results:
            - all_complete: bool
            - incomplete_tasks: List[Dict]
            - failed_tasks: List[Dict]
            - total_tasks: int
            - completed_tasks: int
        """
        try:
            # Load tasks from file
            file_path = Path(self.tasks_file)
            
            if not file_path.exists():
                logger.error(f"Tasks file not found: {self.tasks_file}")
                return {
                    "all_complete": False,
                    "error": f"Tasks file not found: {self.tasks_file}",
                    "incomplete_tasks": [],
                    "failed_tasks": [],
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            tasks = data.get("tasks", [])
            
            if not tasks:
                logger.warning("No tasks found in tasks file")
                return {
                    "all_complete": True,
                    "incomplete_tasks": [],
                    "failed_tasks": [],
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            
            # Analyze task statuses
            completed_tasks = []
            incomplete_tasks = []
            failed_tasks = []
            
            for task in tasks:
                status = task.get("status", "pending").lower()
                
                if status == "completed":
                    completed_tasks.append(task)
                elif status in ["failed", "error"]:
                    failed_tasks.append(task)
                else:
                    # pending, in_progress, or any other status
                    incomplete_tasks.append(task)
            
            all_complete = len(incomplete_tasks) == 0 and len(failed_tasks) == 0
            
            result = {
                "all_complete": all_complete,
                "incomplete_tasks": incomplete_tasks,
                "failed_tasks": failed_tasks,
                "total_tasks": len(tasks),
                "completed_tasks": len(completed_tasks)
            }
            
            logger.info(
                f"Validation result: {len(completed_tasks)}/{len(tasks)} completed, "
                f"{len(incomplete_tasks)} incomplete, {len(failed_tasks)} failed"
            )
            
            return result
        
        except Exception as e:
            logger.exception(f"Error validating task completion: {e}")
            return {
                "all_complete": False,
                "error": str(e),
                "incomplete_tasks": [],
                "failed_tasks": [],
                "total_tasks": 0,
                "completed_tasks": 0
            }
    
    async def judge_and_replan(self, planner, user_input: UserInput, worker) -> Dict:
        """
        Main judge workflow: Validate completion and trigger replanning if needed.
        
        Args:
            planner: The Planner instance to use for replanning
            user_input: The original user input
            worker: The Worker instance to save new plan
        
        Returns:
            Dict with judgment results and actions taken
        """
        logger.info("Judge: Starting validation...")
        
        # Validate current task completion
        validation = await self.validate_task_completion()
        
        if validation.get("all_complete", False):
            logger.info("Judge: All tasks completed successfully!")
            return {
                "status": "success",
                "message": "All tasks completed successfully",
                "validation": validation,
                "replanned": False
            }
        
        # Check if we have incomplete or failed tasks
        incomplete_tasks = validation.get("incomplete_tasks", [])
        failed_tasks = validation.get("failed_tasks", [])
        
        if not incomplete_tasks and not failed_tasks:
            # No tasks or validation error
            error_msg = validation.get("error", "Unknown error")
            logger.error(f"Judge: Validation error - {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "validation": validation,
                "replanned": False
            }
        
        # Tasks are incomplete or failed - need to replan
        logger.warning(
            f"Judge: Found {len(incomplete_tasks)} incomplete and "
            f"{len(failed_tasks)} failed tasks. Triggering replanning..."
        )
        
        # Check retry count to avoid infinite loops
        retry_count = validation.get("retry_count", 0)
        if retry_count >= self.max_retries:
            logger.error(f"Judge: Max retries ({self.max_retries}) reached. Stopping.")
            return {
                "status": "failed",
                "message": f"Max retries ({self.max_retries}) reached. Cannot complete tasks.",
                "validation": validation,
                "replanned": False
            }
        
        # Build a refined prompt for replanning
        replan_prompt = self._build_replan_prompt(
            user_input,
            incomplete_tasks,
            failed_tasks,
            retry_count
        )
        
        # Create new user input for replanning
        replan_user_input = UserInput(
            session_id=user_input.session_id,
            message=replan_prompt,
            document_text=user_input.document_text
        )
        
        # Trigger replanning
        logger.info("Judge: Calling planner for replanning...")
        new_plan_data = await planner.create_plan(replan_user_input)
        
        # Save the new plan via worker
        logger.info("Judge: Saving replanned tasks...")
        save_result = await worker.save_tasks_to_file(new_plan_data)
        
        # Update retry count in the tasks file
        await self._update_retry_count(retry_count + 1)
        
        return {
            "status": "replanned",
            "message": f"Replanned due to {len(incomplete_tasks)} incomplete and {len(failed_tasks)} failed tasks",
            "validation": validation,
            "replanned": True,
            "new_plan": new_plan_data,
            "save_result": save_result,
            "retry_count": retry_count + 1
        }
    
    def _build_replan_prompt(
        self,
        original_input: UserInput,
        incomplete_tasks: List[Dict],
        failed_tasks: List[Dict],
        retry_count: int
    ) -> str:
        """
        Build a detailed prompt for replanning based on incomplete/failed tasks.
        """
        prompt_parts = [
            f"Original request: {original_input.message}",
            f"\nRetry attempt: {retry_count + 1}/{self.max_retries}",
            "\n\nThe following tasks need to be addressed:"
        ]
        
        if incomplete_tasks:
            prompt_parts.append("\n\nIncomplete tasks:")
            for i, task in enumerate(incomplete_tasks, 1):
                task_desc = task.get("task", task.get("description", "Unknown task"))
                prompt_parts.append(f"{i}. {task_desc} (Status: {task.get('status', 'pending')})")
        
        if failed_tasks:
            prompt_parts.append("\n\nFailed tasks:")
            for i, task in enumerate(failed_tasks, 1):
                task_desc = task.get("task", task.get("description", "Unknown task"))
                error = task.get("error", "Unknown error")
                prompt_parts.append(f"{i}. {task_desc} (Error: {error})")
        
        prompt_parts.append(
            "\n\nPlease create a new plan to complete these tasks. "
            "Consider alternative approaches if previous attempts failed."
        )
        
        return "\n".join(prompt_parts)
    
    async def _update_retry_count(self, retry_count: int):
        """
        Update the retry count in the tasks file metadata.
        """
        try:
            file_path = Path(self.tasks_file)
            
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                data["retry_count"] = retry_count
                data["last_retry_timestamp"] = self._get_timestamp()
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                logger.info(f"Updated retry count to {retry_count}")
        except Exception as e:
            logger.exception(f"Failed to update retry count: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
