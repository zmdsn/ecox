"""财务分析工具"""
from typing import Dict, Any, List
from .base import Tool
from ...utils import code_format


class FinancialAnalysisTool(Tool):
    """财务分析工具

    调用 FinancialAnalysisService 分析股票财务数据
    """

    @property
    def name(self) -> str:
        return "financial_analysis"

    @property
    def description(self) -> str:
        return "分析股票财务数据，包括ROE、毛利率、净利润、现金流、偿债能力、成长能力等指标"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "股票代码（如 601318 或 SH601318）"
                },
                "modules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "分析模块列表（profitability, cash_flow, solvency, efficiency, growth, valuation）",
                    "default": ["profitability", "solvency"]
                },
                "report_date": {
                    "type": "string",
                    "description": "报告日期（如 2024-09-30，默认最新）"
                }
            },
            "required": ["stock_code"]
        }

    async def execute(
        self,
        stock_code: str = None,
        modules: List[str] = None,
        report_date: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """执行财务分析

        Args:
            stock_code: 股票代码
            modules: 分析模块列表
            report_date: 报告日期
            **kwargs: 其他参数（兼容基类接口）

        Returns:
            财务分析结果
        """
        # 如果没有提供股票代码，返回提示
        if not stock_code:
            return {
                "error": "缺少股票代码",
                "hint": "请提供要分析的股票代码"
            }
        from ...services.financial_analysis_service import FinancialAnalysisService

        # 格式化股票代码
        formatted_code = code_format(stock_code)

        # 默认模块
        if modules is None:
            modules = ["profitability", "solvency"]

        # 调用服务
        service = FinancialAnalysisService()
        result = await self._get_analysis_result(
            service, formatted_code, modules, report_date
        )

        return result

    async def _get_analysis_result(
        self,
        service,
        stock_code: str,
        modules: List[str],
        report_date: str = None
    ) -> Dict[str, Any]:
        """获取分析结果（异步包装）"""
        # FinancialAnalysisService.calculate_metrics 是同步方法
        # 这里用 run_in_executor 执行
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: service.calculate_metrics(
                stock_code=stock_code,
                report_date=report_date,
                modules=modules
            )
        )
