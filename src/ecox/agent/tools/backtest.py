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
        stock_code: str = None,
        start_date: str = None,
        end_date: str = None,
        strategy: str = "DoubleMA_Strategy",
        initial_cash: float = 1000000,
        **kwargs
    ) -> Dict[str, Any]:
        """执行回测

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            strategy: 策略名称
            initial_cash: 初始资金
            **kwargs: 其他参数（兼容基类接口）

        Returns:
            回测结果或错误信息
        """
        # 验证必需参数
        if not stock_code:
            return {
                "error": "缺少股票代码",
                "hint": "请提供要回测的股票代码"
            }

        if not start_date or not end_date:
            return {
                "error": "缺少日期范围",
                "hint": "请提供开始日期和结束日期（YYYY-MM-DD格式）",
                "stock_code": stock_code
            }
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
