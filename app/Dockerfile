# 1. Use a lightweight Python base
FROM python:3.11-slim

# 2. Install uv into the container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Set the working directory
WORKDIR /app

# 4. Copy your requirements file
COPY requirements.txt .

# 5. Install dependencies to the container's system python
# This avoids the "creating .venv" log messages later
RUN uv pip install --system -r requirements.txt

# 6. Copy the rest of your project code
COPY . .

# 7. Run the server
# --quiet ensures no extra logs mess up the MCP communication
ENV PYTHONPATH="/app"
CMD ["python", "-u", "server/orchestrator.py"]