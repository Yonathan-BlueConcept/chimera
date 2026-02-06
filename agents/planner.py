# planner.py
from models.model import UserInput, Plan


class Planner:
    def create_plan(self, user_input: UserInput) -> Plan:
        """
        Decide WHAT needs to be done.
        No tools. No execution.
        """

        if user_input.file_path:
            return Plan(
                task="analyze_document",
                parameters={
                    "question": user_input.message,
                    "file_path": user_input.file_path
                }
            )

        return Plan(
            task="general_chat",
            parameters={
                "question": user_input.message
            }
        )
