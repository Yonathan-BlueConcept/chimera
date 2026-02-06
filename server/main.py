# server.py
from mcp.server import Server

server = Server("chimera-orchestrator")


@server.tool()
async def chat(message: str, document: str | None = None) -> str:
    """
    Use this tool to send a message and an optional document to the Chimera orchestrator.

    Args:
        message: The main query or instruction for the orchestrator.
        document: Optional text content or code to be processed.
    """
    return f"RECEIVED FROM VS CODE CHAT\n\nMessage: <<< {message} >>>"


if __name__ == "__main__":
    server.run_stdio()
