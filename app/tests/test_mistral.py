import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agents.mistral import MistralProvider, get_reasoning_response

@pytest.fixture
def mock_mistral_client():
    with patch("agents.mistral.Mistral") as mock:
        yield mock

def test_mistral_provider_singleton(mock_mistral_client):
    # Reset singleton for testing
    MistralProvider._client = None
    
    client1 = MistralProvider.get_client()
    client2 = MistralProvider.get_client()
    
    assert client1 is client2
    mock_mistral_client.assert_called_once()

@pytest.mark.asyncio
async def test_get_reasoning_response_success():
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"tasks": ["task1"]}'))
    ]
    
    # Mock the singleton client
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(return_value=mock_response)
    
    with patch.object(MistralProvider, "get_client", return_value=mock_client):
        result = await get_reasoning_response("test prompt")
        
        assert result == {"tasks": ["task1"]}
        mock_client.chat.complete_async.assert_called_once()

@pytest.mark.asyncio
async def test_get_reasoning_response_invalid_structure():
    mock_response = MagicMock()
    mock_response.choices = [] # Empty choices
    
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(return_value=mock_response)
    
    with patch.object(MistralProvider, "get_client", return_value=mock_client):
        result = await get_reasoning_response("test prompt")
        
        assert "error" in result
        assert "Invalid response structure" in result["error"]
