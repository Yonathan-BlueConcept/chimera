# planner.py
import json
import logging
from models.model import UserInput, Plan
from agents.mistral import MistralProvider

logger = logging.getLogger("chimera.planner")

class Planner:
    # Changed to 'async def' to allow the use of 'await'
    async def create_plan(self, user_input: UserInput) -> dict:
        """
        Decide WHAT needs to be done.
        Uses high-complexity reasoning (Mistral Large) to generate a task list.
        """

        mistral_client = MistralProvider.get_client()
        
        # Use await to handle the asynchronous call to Mistral
        # This aligns with the 'Reasoning Head' pattern for planners [cite: 89]
        response = await mistral_client.chat.complete_async(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": "You are the Planner. Decompose goals into a JSON list of tasks."},
                {"role": "user", "content": user_input.message}
            ],
            response_format={"type": "json_object"} # Recommended for Schema 1: Agent Task [cite: 289]
        )

        # The provider may return different shaped responses depending on SDK
        # Normalize to a Python object (dict/list) or fallback to string
        plan_output = None
        try:
            # Mistral SDK returns a response object with choices
            if hasattr(response, "choices") and len(response.choices) > 0:
                choice = response.choices[0]
                # Access message.content
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content
                    # Parse JSON content
                    if isinstance(content, str):
                        try:
                            plan_output = json.loads(content)
                        except Exception:
                            logger.warning("Could not parse content as JSON, returning as string")
                            plan_output = content
                    else:
                        plan_output = content
                else:
                    logger.error("Response choice does not have message.content")
                    plan_output = {"error": "Invalid response structure"}
            else:
                logger.error("Response does not have choices")
                plan_output = {"error": "Invalid response structure"}
        except Exception as e:
            logger.exception("Planner: failed to normalize response")
            plan_output = {"error": str(e)}

        logger.info("from planner mistral output: %s", plan_output)
        return plan_output
      