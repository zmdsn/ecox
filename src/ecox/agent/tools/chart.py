"""图表生成工具"""
from typing import Dict, Any
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.io as pio
import base64
from .base import Tool
from ...database import get_db_session
from ... import models
from ...utils import code_format

# 全局 Kaleido 配置
pio.defaults.default_width = 1200
pio.defaults.default_height = 600
pio.defaults.default_format = "png"
pio.defaults.default_scale = 1  # 高清


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

    def _to_base64(self, fig: go.Figure) -> str:
        """将 Plotly 图表转换为 base64 编码

        Args:
            fig: Plotly 图表对象

        Returns:
            base64 编码的字符串

        Note:
            在 WSL 环境中，Kaleido 可能无法正常工作。
            如果遇到 kaleido_scopes 错误，需要在非 WSL 环境中运行。
        """
        try:
            # 转换为图片
            img_bytes = fig.to_image(format="png")
        except Exception as e:
            # 捕获 Kaleido 错误并提供有用的信息
            if "kaleido_scopes" in str(e):
                raise RuntimeError(
                    "Kaleido 无法初始化。这通常发生在 WSL 环境中。"
                    "解决方案：1) 在非 WSL 环境中运行 2) 安装并配置 xvfb "
                    "3) 使用原生 Linux 或 macOS 环境"
                ) from e
            raise

        # 编码为 base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        return img_base64

    async def _plot_price_trend(
        self,
        stock_code: str,
        period: str = "30d",
        show_ma: bool = False,
        show_volume: bool = True
    ) -> Dict[str, Any]:
        """绘制股价走势图

        Args:
            stock_code: 股票代码
            period: 时间范围
            show_ma: 是否显示均线
            show_volume: 是否显示成交量

        Returns:
            包含 base64 图片的字典
        """
        # 计算日期范围
        period_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "180d": 180,
            "1y": 365,
            "3y": 365 * 3,
            "5y": 365 * 5
        }
        days = period_map.get(period, 30)
        start_date = datetime.now() - timedelta(days=days)

        # 查询历史数据
        formatted_code = code_format(stock_code)
        with get_db_session() as session:
            data = session.query(models.StockDailyData).filter(
                models.StockDailyData.stock_code == formatted_code,
                models.StockDailyData.trade_date >= start_date
            ).order_by(models.StockDailyData.trade_date.asc()).all()

        if not data:
            return {
                "error": f"未找到股票 {stock_code} 的历史数据",
                "stock_code": stock_code,
                "suggestion": "请检查股票代码或尝试其他时间范围"
            }

        # 提取数据
        dates = [d.trade_date for d in data]
        prices = [float(d.close) for d in data]
        stock_name = data[0].stock_code if hasattr(data[0], 'stock_code') else stock_code

        # 创建图表
        fig = go.Figure()

        # 添加收盘价折线
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name='收盘价',
            line=dict(color='#EF4444', width=2)
        ))

        # 设置布局
        fig.update_layout(
            title=f'{stock_code} {stock_name} - 股价走势图（近{period}）',
            xaxis_title='日期',
            yaxis_title='价格（元）',
            hovermode='x unified',
            template='plotly_white',
            font=dict(family='SimHei, Arial', size=12),
            width=1200,
            height=600
        )

        # 转换为 base64
        img_base64 = self._to_base64(fig)

        return {
            "chart_type": "price_trend",
            "image_base64": img_base64,
            "format": "png",
            "width": 1200,
            "height": 600,
            "title": f"{stock_code} {stock_name} - 股价走势图（近{period}）",
            "data_summary": {
                "start_date": str(dates[0]),
                "end_date": str(dates[-1]),
                "data_points": len(dates)
            }
        }
