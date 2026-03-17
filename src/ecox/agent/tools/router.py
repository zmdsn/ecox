"""工具路由器"""
import logging
from typing import Dict, Any, List
from .financial import FinancialAnalysisTool
from .market import MarketDataTool
from .data import DataQueryTool
from .backtest import BacktestTool
from .chart import ChartTool

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
            "chart": ChartTool(),
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
        """根据上下文智能选择工具

        改进：根据问题类型智能选择工具，避免混淆
        - 行情查询（股价、最新价、涨跌幅等）→ 只调用 market_data
        - 财务分析（ROE、盈利能力等）→ 只调用 financial_analysis
        - 模糊或综合问题 → 调用两个工具
        """
        tools = []

        # 提取消息内容（转换为小写便于匹配）
        content = " ".join([msg.content for msg in context.current_messages]).lower()

        # 定义关键词分类
        market_keywords = [
            "股价", "最新价", "实时", "涨跌幅", "行情", "收盘", "开盘",
            "最高", "最低", "成交量", "成交额", "市值", "价格",
            "最新", "当前", "现在", "今日"
        ]
        financial_keywords = [
            "财务", "分析", "roe", "盈利", "偿债", "现金流", "毛利率",
            "净利润", "资产", "负债", "成长性", "杜邦", "营运",
            "指标", "能力", "状况"
        ]

        # 图表相关关键词
        chart_keywords = [
            "图表", "走势图", "趋势图", "K线", "蜡烛图", "收益曲线",
            "可视化", "绘图", "画图", "生成图", "展示图"
        ]

        # 判断问题类型
        is_market_query = any(kw in content for kw in market_keywords)
        is_financial_query = any(kw in content for kw in financial_keywords)

        # 有股票代码实体时，根据问题类型智能选择工具
        if context.entities.stock_codes:
            if is_market_query and not is_financial_query:
                # 纯行情查询 → 只调用行情工具（避免返回历史财务数据）
                tools.append("market_data")
                logger.info(f"✅ 选择行情工具（仅行情）: 检测到行情查询关键词")
            elif is_financial_query and not is_market_query:
                # 纯财务分析 → 只调用财务工具（避免不必要的行情查询）
                tools.append("financial_analysis")
                logger.info(f"✅ 选择财务工具（仅财务）: 检测到财务分析关键词")
            else:
                # 模糊或两者都有 → 调用两个工具（综合分析）
                tools.append("financial_analysis")
                tools.append("market_data")
                logger.info(f"✅ 选择双工具（综合分析）: 问题模糊或包含多维度需求")
        else:
            # 没有股票代码但有其他实体时，默认行为
            if context.entities.stock_codes:
                # 兼容旧逻辑：有股票代码就调用两个工具
                tools.append("financial_analysis")
                tools.append("market_data")

        # 有日期实体
        if context.entities.dates:
            tools.append("data_query")

        # 回测和策略关键词
        if "回测" in content or "策略" in content:
            if "backtest" not in tools:
                tools.append("backtest")

        # SQL查询关键词
        if "查询" in content or "SQL" in content or "sql" in content.lower():
            if "data_query" not in tools:
                tools.append("data_query")

        # 图表生成关键词
        if any(kw in content for kw in chart_keywords):
            if "chart" not in tools:
                tools.append("chart")

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

        elif tool.name == "chart":
            # 准备图表参数
            content = " ".join([msg.content for msg in context.current_messages]).lower()
            chart_type = "price_trend"  # 默认

            # 根据关键词推断图表类型
            if "财务" in content or "指标" in content:
                chart_type = "financial_trend"
            elif "回测" in content or "收益" in content:
                chart_type = "backtest"
            elif "杜邦" in content:
                chart_type = "dupont"

            return {
                "chart_type": chart_type,
                "stock_code": context.entities.stock_codes[0] if context.entities.stock_codes else None,
                "period": "30d"
            }

        return {}
