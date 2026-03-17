"""图表生成工具"""
from typing import Dict, Any
from .base import Tool


class ChartTool(Tool):
    """专业金融图表生成工具"""

    @property
    def name(self) -> str:
        return "chart"

    @property
    def description(self) -> str:
        return "生成股票相关的专业金融图表（股价走势、财务趋势、回测收益、杜邦分析等），返回 base64 编码的 PNG 图片"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["price_trend", "financial_trend", "backtest", "dupont"],
                    "description": "图表类型"
                },
                "stock_code": {
                    "type": "string",
                    "description": "股票代码（必需）"
                },
                "period": {
                    "type": "string",
                    "default": "30d",
                    "description": "时间范围：7d|30d|90d|180d|1y|3y|5y"
                },
                "indicator": {
                    "type": "string",
                    "description": "财务指标（用于财务趋势图）"
                },
                "show_ma": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否显示均线"
                }
            },
            "required": ["chart_type", "stock_code"]
        }

    async def execute(self, chart_type: str, stock_code: str, **kwargs) -> Dict[str, Any]:
        """生成图表

        Args:
            chart_type: 图表类型
            stock_code: 股票代码
            **kwargs: 其他参数

        Returns:
            包含 base64 图片的字典
        """
        # 参数验证
        if chart_type not in ["price_trend", "financial_trend", "backtest", "dupont"]:
            return {
                "error": f"不支持的图表类型: {chart_type}",
                "supported_types": ["price_trend", "financial_trend", "backtest", "dupont"]
            }

        # 路由到具体的绘图方法
        if chart_type == "price_trend":
            return await self._plot_price_trend(stock_code, **kwargs)
        elif chart_type == "financial_trend":
            return await self._plot_financial_trend(stock_code, **kwargs)
        elif chart_type == "backtest":
            return await self._plot_backtest_returns(**kwargs)
        elif chart_type == "dupont":
            return await self._plot_dupont_analysis(stock_code, **kwargs)
