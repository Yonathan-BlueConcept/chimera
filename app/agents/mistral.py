# llm_provider.py
import os
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MistralProvider:
    _client = None

    @classmethod
    def get_client(cls) -> Mistral:
        """
        Returns a singleton instance of the Mistral client.
        Ensures the API key is only read and the client initialized once.
        """
        if cls._client is None:
            # api_key = os.getenv("MISTRAL_API_KEY")
            api_key="KzgBrpEXhq0hO91B2kSnZAM9jZmT1yAm"
            if not api_key:
                raise ValueError("MISTRAL_API_KEY not found in environment")
            
            # Initialize the shared client
            cls._client = Mistral(api_key=api_key)
        return cls._client

# Optional helper for a common reasoning prompt used by Planners
async def get_reasoning_response(prompt: str, model: str = "mistral-small-latest", type=""):
    import json
    import logging
    logger = logging.getLogger("chimera.mistral")
    
    client = MistralProvider.get_client()
    response = await client.chat.complete_async(
        model=model,
        messages=[{"role": "user", "content": type + prompt}],
        response_format={"type": "json_object"}  # Essential for Task DAGs [cite: 115, 290]
    )
    
    # Parse and return the content
    try:
        if hasattr(response, "choices") and len(response.choices) > 0:
            content = response.choices[0].message.content
            if isinstance(content, str):
                return json.loads(content)
            return content
        else:
            logger.error("Invalid response structure")
            return {"error": "Invalid response structure"}
    except Exception as e:
        logger.exception("Failed to parse response")
        return {"error": str(e)}
