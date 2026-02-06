# System Overview

This application is an agentic system that processes user input from the
VS Code Chat interface and executes tasks through a planner–worker workflow.

## High-Level Flow

1. The system accepts a user prompt from the VS Code Chat system.
2. The prompt is passed to the Planner component.
3. The Planner uses a Mistral-based LLM to decompose the prompt into a set of
   small, manageable tasks.
4. The generated tasks are passed to the Worker component.
5. The Worker writes the tasks to a `tasks.json` file.
6. The Judge component verifies that the tasks were written successfully.
7. If verification fails, the Judge triggers a retry by re-invoking the
   Planner and Worker components.

## Core Components

### Planner
- Responsible for task decomposition.
- Uses a Mistral LLM to transform a user prompt into structured tasks.
- Produces a task list suitable for execution by the Worker.

### Worker
- Responsible for task execution.
- Persists planner-generated tasks to `tasks.json`.

### Judge
- Responsible for validation and reliability.
- Verifies the integrity and successful creation of `tasks.json`.
- Initiates retries when task persistence fails.

## System Guarantees
- User input is always processed through the Planner before execution.
- Tasks are persisted before being considered valid.
- Failed task writes are retried automatically.

## Out of Scope
- Long-term task storage beyond `tasks.json`
- User authentication or authorization
- UI rendering or presentation logic
