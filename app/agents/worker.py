# worker.py
from models.model import Plan, WorkResult


class Worker:
    def execute(self, plan: Plan, document_text: str) -> WorkResult:
        # VERY naive implementation for now
        # Later this becomes an LLM call

        if "risk" in plan.question.lower():
            answer = "The document mentions risks related to system complexity, security, and operational scalability."
        else:
            answer = "The document discusses architectural and operational considerations."

        return WorkResult(answer=answer)
