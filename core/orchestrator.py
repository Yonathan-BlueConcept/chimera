# orchestrator.py
from planner import Planner
from agents.worker import Worker
from models.model import UserInput, WorkResult


class Orchestrator:
    def __init__(self):
        self.planner = Planner()
        self.worker = Worker()

    def handle(self, user_input: UserInput) -> WorkResult:
        print(f"this is the user input {user_input.message}")
        plan = self.planner.create_plan(user_input)
        result = self.worker.execute(plan, user_input.document_text)
        return result
