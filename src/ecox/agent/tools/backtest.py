"""回测工具"""
import subprocess
import re
from typing import Dict, Any
from .base import Tool
from ...utils import code_format


class BacktestTool(Tool):
    """策略回测工具"""

    @property
    def name(self) -> str:
        return "backtest"

    @property
    def description(self) -> str:
        return "对股票进行策略回测，支持双均线、MACD、布林带等策略"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "股票代码"
                },
                "strategy": {
                    "type": "string",
                    "description": "策略名称（DoubleMA_Strategy, MacdCross, BollingerBandsBreakout等）",
                    "default": "DoubleMA_Strategy"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "initial_cash": {
                    "type": "number",
                    "description": "初始资金",
                    "default": 1000000
                }
            },
            "required": ["stock_code", "start_date", "end_date"]
        }

    async def execute(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        strategy: str = "DoubleMA_Strategy",
        initial_cash: float = 1000000
    ) -> Dict[str, Any]:
        """执行回测"""
        import asyncio

        formatted_code = code_format(stock_code)

        # 运行回测脚本
        cmd = [
            "uv", "run", "python", "main.py",
            "--stock", formatted_code,
            "--strategy", strategy,
            "--start", start_date,
            "--end", end_date,
            "--cash", str(initial_cash)
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/home/zmdsn/ecox"  # 项目根目录
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {
                    "error": "回测执行失败",
                    "stderr": stderr.decode(),
                    "stock_code": formatted_code
                }

            # 解析输出
            output = stdout.decode()
            return self._parse_backtest_output(output, formatted_code)

        except Exception as e:
            return {
                "error": str(e),
                "stock_code": formatted_code
            }

    def _parse_backtest_output(self, output: str, stock_code: str) -> Dict[str, Any]:
        """解析回测输出"""
        result = {
            "stock_code": stock_code,
            "output": output
        }

        # 尝试提取关键指标
        sharpe_match = re.search(r'Sharpe Ratio[:\s]+([-\d.]+)', output)
        if sharpe_match:
            result["sharpe_ratio"] = float(sharpe_match.group(1))

        drawdown_match = re.search(r'Max Drawdown[:\s]+([-\d.]+)%?', output)
        if drawdown_match:
            result["max_drawdown"] = float(drawdown_match.group(1))

        return result
