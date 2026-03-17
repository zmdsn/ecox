"""工具路由器"""
import logging
from typing import Dict, Any, List
from .financial import FinancialAnalysisTool
from .market import MarketDataTool
from .data import DataQueryTool
from .backtest import BacktestTool

logger = logging.getLogger(__name__)


class ToolRouter:
    """工具路由和编排

    根据对话上下文选择并执行相应的工具
    """

    def __init__(self):
        """初始化路由器"""
        self.tools: Dict[str, Any] = {
            "financial_analysis": FinancialAnalysisTool(),
            "market_data": MarketDataTool(),
            "data_query": DataQueryTool(),
            "backtest": BacktestTool(),
        }

    async def execute(self, context) -> Dict[str, Any]:
        """根据上下文执行工具

        Args:
            context: 对话上下文

        Returns:
            工具执行结果字典
        """
        # 选择需要调用的工具
        tools_to_call = self._select_tools(context)

        results = {}
        for tool_name in tools_to_call:
            tool = self.tools[tool_name]

            # 准备参数
            kwargs = self._prepare_args(tool, context)

            # 执行工具
            try:
                result = await tool.execute(**kwargs)
                results[tool_name] = result
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                results[tool_name] = {"error": str(e)}

        return results

    def _select_tools(self, context) -> List[str]:
        """根据上下文选择工具"""
        tools = []

        # 有股票代码实体
        if context.entities.stock_codes:
            tools.append("financial_analysis")
            tools.append("market_data")

        # 有日期实体
        if context.entities.dates:
            tools.append("data_query")

        # 检查关键词
        content = " ".join([msg.content for msg in context.current_messages])

        if "回测" in content or "策略" in content:
            tools.append("backtest")

        if "查询" in content or "SQL" in content or "sql" in content.lower():
            if "data_query" not in tools:
                tools.append("data_query")

        return tools

    def _prepare_args(self, tool, context) -> Dict[str, Any]:
        """准备工具参数"""
        if tool.name == "financial_analysis":
            return {
                "stock_code": context.entities.stock_codes[0] if context.entities.stock_codes else None,
                "modules": ["profitability", "solvency", "cash_flow"]
            }

        elif tool.name == "market_data":
            return {
                "stock_code": context.entities.stock_codes[0] if context.entities.stock_codes else None
            }

        elif tool.name == "backtest":
            # 从实体中提取日期
            dates = context.entities.dates
            return {
                "stock_code": context.entities.stock_codes[0] if context.entities.stock_codes else None,
                "start_date": dates[0] if len(dates) > 0 else "2023-01-01",
                "end_date": dates[1] if len(dates) > 1 else "2024-12-31"
            }

        elif tool.name == "data_query":
            # 构建简单查询
            stock_code = context.entities.stock_codes[0] if context.entities.stock_codes else None
            if stock_code:
                return {
                    "sql": f"SELECT * FROM stock_daily_data WHERE stock_code = '{stock_code}' ORDER BY trade_date DESC LIMIT 10"
                }
            return {}

        return {}
