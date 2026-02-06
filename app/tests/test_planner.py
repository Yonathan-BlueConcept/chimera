import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from agents.planner import Planner
from models.model import UserInput
from agents.mistral import MistralProvider

@pytest.fixture
def planner():
    return Planner()

@pytest.fixture
def user_input():
    return UserInput(
        session_id="test-session",
        message="test message",
        document_text="test document"
    )

@pytest.mark.asyncio
async def test_create_plan_success(planner, user_input):
    # Setup mock response from Mistral
    expected_plan = {"tasks": [{"id": 1, "task": "Test task"}]}
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(expected_plan)))
    ]
    
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(return_value=mock_response)
    
    with patch.object(MistralProvider, "get_client", return_value=mock_client):
        result = await planner.create_plan(user_input)
        
        assert result == expected_plan
        # Verify the call to Mistral
        mock_client.chat.complete_async.assert_called_once()
        args, kwargs = mock_client.chat.complete_async.call_args
        assert kwargs["model"] == "mistral-small-latest"
        assert kwargs["messages"][1]["content"] == "test message"

@pytest.mark.asyncio
async def test_create_plan_non_json_content(planner, user_input):
    # Setup mock response with plain text instead of JSON
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Plain text response"))
    ]
    
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(return_value=mock_response)
    
    with patch.object(MistralProvider, "get_client", return_value=mock_client):
        result = await planner.create_plan(user_input)
        
        # Should return the plain text content
        assert result == "Plain text response"

@pytest.mark.asyncio
async def test_create_plan_api_error(planner, user_input):
    # Setup mock to raise an exception
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(side_effect=Exception("API Error"))
    
    with patch.object(MistralProvider, "get_client", return_value=mock_client):
        # The code in planner.py catches exceptions in create_plan? 
        # Actually, looking at planner.py, chat.complete_async is called outside the try-except block
        # that handles normalization. Let's check planner.py content again.
        
        with pytest.raises(Exception) as excinfo:
            await planner.create_plan(user_input)
        
        assert "API Error" in str(excinfo.value)
