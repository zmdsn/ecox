"""Tests for BacktestTool."""
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from ecox.agent.tools.backtest import BacktestTool


def test_backtest_tool_properties():
    """测试回测工具属性"""
    tool = BacktestTool()
    assert tool.name == "backtest"
    assert "回测" in tool.description


def test_backtest_tool_execute():
    """测试执行回测"""
    import asyncio
    from unittest.mock import AsyncMock
    tool = BacktestTool()

    # Mock subprocess
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"Sharpe Ratio: 1.5\nMax Drawdown: -10%", b""))

    with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_subproc:
        mock_subproc.return_value = mock_proc

        result = asyncio.run(tool.execute(
            stock_code="601318",
            strategy="DoubleMA_Strategy",
            start_date="2023-01-01",
            end_date="2024-12-31"
        ))

        assert "sharpe_ratio" in result or "output" in result
        if "sharpe_ratio" in result:
            assert result["sharpe_ratio"] == 1.5
