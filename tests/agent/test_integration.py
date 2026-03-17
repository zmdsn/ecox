"""Ecox AI Agent 集成测试

测试完整的对话流程和各组件协作
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from ecox.agent import EcoxA
from ecox.agent.models.message import Message


def test_full_conversation_flow():
    """测试完整的对话流程（带工具调用）"""
    agent = EcoxA(model="gpt-4")

    messages = [
        Message(role="user", content="分析中国平安601318的财务状况", session_id="test-integration-1")
    ]

    # Mock ToolRouter
    with patch.object(agent.tool_router, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {
            "financial_analysis": {
                "stock_code": "SH601318",
                "stock_name": "中国平安",
                "roe": 15.2
            }
        }

        # Mock LLM API
        with patch('ecox.agent.agent.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "根据财务分析，中国平安(601318)的ROE为15.2%。"
                    }
                }]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Execute
            response = asyncio.run(agent.chat(messages))

            # Verify
            assert response is not None
            mock_execute.assert_called_once()


def test_conversation_without_tools():
    """测试不需要工具的对话"""
    agent = EcoxA(model="gpt-4")

    messages = [
        Message(role="user", content="你好", session_id="test-no-tools")
    ]

    # Mock LLM API
    with patch('ecox.agent.agent.httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "你好！我是Ecox。"
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        response = asyncio.run(agent.chat(messages))

        assert response is not None
