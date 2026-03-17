"""Tests for Tool base class."""
import pytest
import asyncio
from ecox.agent.tools.base import Tool


class DummyTool(Tool):
    """测试用的虚拟工具"""

    @property
    def name(self) -> str:
        return "dummy_tool"

    @property
    def description(self) -> str:
        return "A dummy tool for testing"

    async def execute(self, **kwargs):
        return {"result": "success", **kwargs}


def test_tool_properties():
    """测试工具属性"""
    tool = DummyTool()
    assert tool.name == "dummy_tool"
    assert tool.description == "A dummy tool for testing"


def test_tool_parameters_default():
    """测试默认参数定义"""
    tool = DummyTool()
    params = tool.parameters
    assert params["type"] == "object"
    assert "properties" in params


def test_tool_execute():
    """测试工具执行"""
    tool = DummyTool()
    result = asyncio.run(tool.execute(arg1="value1"))
    assert result["result"] == "success"
    assert result["arg1"] == "value1"


def test_tool_abstract_cannot_instantiate():
    """测试不能直接实例化抽象基类"""
    with pytest.raises(TypeError):
        Tool()
