"""统一财务分析服务"""
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import desc

from ecox.calculators import (
    BaseCalculator,
    CashFlowCalculator,
    EfficiencyCalculator,
    GrowthCalculator,
    ProfitabilityCalculator,
    SolvencyCalculator,
    ValuationCalculator,
)
from ecox.database import get_db_session
from ecox import models
from .lazy_loading_service import LazyLoadingService

logger = logging.getLogger(__name__)


class FinancialAnalysisService:
    """统一财务分析服务

    整合所有财务指标计算器，提供统一的财务分析接口。
    支持从数据库获取财务数据，调用各计算器进行计算，并保存结果。
    """

    def __init__(self):
        """初始化服务，创建所有计算器实例"""
        self.calculators: dict[str, BaseCalculator] = {
            "profitability": ProfitabilityCalculator(),
            "cash_flow": CashFlowCalculator(),
            "solvency": SolvencyCalculator(),
            "efficiency": EfficiencyCalculator(),
            "growth": GrowthCalculator(),
            "valuation": ValuationCalculator(),
        }
        self.lazy_loader = LazyLoadingService()

    def _get_financial_data(
        self, stock_code: str, report_date: str | None = None
    ) -> dict[str, Any]:
        """获取财务数据（使用懒加载服务）

        使用 LazyLoadingService 自动获取和缓存财务数据。
        如果数据库中没有数据，会自动从 akshare 下载。

        Args:
            stock_code: 股票代码
            report_date: 报告日期（可选，默认最新）

        Returns:
            包含 profit_sheet, balance_sheet, cash_flow_sheet 的字典
        """
        # 使用懒加载服务获取数据
        data = self.lazy_loader.get_financial_data(
            stock_code=stock_code,
            report_date=report_date,
            force_refresh=False
        )

        # 转换为服务所需的格式
        result = {
            "profit_sheet": data.get('profit_sheet', {}),
            "balance_sheet": data.get('balance_sheet', {}),
            "cash_flow_sheet": data.get('cash_flow_sheet', {}),
            "stock_name": data.get('stock_name'),
            "report_date": data.get('report_date'),
            "report_type": data.get('report_type'),
        }

        return result

    def calculate_metrics(
        self,
        stock_code: str,
        report_date: str | None = None,
        modules: list[str] | None = None,
        market_data: dict[str, Any] | None = None,
        financial_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """计算财务指标

        Args:
            stock_code: 股票代码
            report_date: 报告日期（可选，默认最新）
            modules: 计算模块列表（可选，默认全部）
                支持的模块: profitability, cash_flow, solvency,
                           efficiency, growth, valuation
            market_data: 市场数据（可选），用于估值计算
                包括 market_cap, total_debt, cash, ebitda, earnings_growth 等
            financial_data: 财务数据（可选，用于测试时直接传入）

        Returns:
            完整的财务指标结果，包含:
            - stock_code: 股票代码
            - stock_name: 股票名称
            - report_date: 报告日期
            - report_type: 报告类型
            - 各模块的计算结果
        """
        # 获取财务数据（如果未提供）
        if financial_data is None:
            financial_data = self._get_financial_data(stock_code, report_date)

        # 确定要计算的模块
        if modules is None:
            modules = list(self.calculators.keys())

        # 验证模块名称
        valid_modules = set(self.calculators.keys())
        invalid_modules = set(modules) - valid_modules
        if invalid_modules:
            logger.warning(f"未知的计算模块: {invalid_modules}")

        # 初始化结果
        result = {
            "stock_code": stock_code,
            "stock_name": financial_data.get("stock_name"),
            "report_date": financial_data.get("report_date"),
            "report_type": financial_data.get("report_type"),
        }

        # 调用各计算器计算指标
        for module_name in modules:
            if module_name not in valid_modules:
                continue

            calculator = self.calculators[module_name]
            try:
                module_result = calculator.calculate(
                    profit_sheet=financial_data["profit_sheet"],
                    balance_sheet=financial_data["balance_sheet"],
                    cash_flow_sheet=financial_data["cash_flow_sheet"],
                    market_data=market_data,
                )
                result.update(module_result)
            except Exception as e:
                logger.error(f"计算 {stock_code} 的 {module_name} 指标失败: {e}")

        return result

    def save_metrics(self, stock_code: str, metrics: dict[str, Any]) -> bool:
        """保存计算结果到数据库

        Args:
            stock_code: 股票代码
            metrics: 计算得到的财务指标字典

        Returns:
            保存成功返回 True，失败返回 False
        """
        try:
            with get_db_session() as session:
                # 查找是否已存在记录
                existing = session.query(models.StockFinancialMetrics).filter(
                    models.StockFinancialMetrics.stock_code == stock_code,
                    models.StockFinancialMetrics.report_date == metrics.get("report_date"),
                ).first()

                if existing:
                    # 更新现有记录
                    self._update_metrics_record(existing, metrics)
                    existing.update_time = datetime.now()
                else:
                    # 创建新记录
                    record = models.StockFinancialMetrics(
                        stock_code=stock_code,
                        stock_name=metrics.get("stock_name"),
                        report_date=metrics.get("report_date"),
                        report_type=metrics.get("report_type"),
                    )
                    self._update_metrics_record(record, metrics)
                    session.add(record)

                session.commit()
                return True
        except Exception as e:
            logger.error(f"保存 {stock_code} 财务指标失败: {e}")
            return False

    def _update_metrics_record(
        self, record: models.StockFinancialMetrics, metrics: dict[str, Any]
    ) -> None:
        """更新指标记录的字段

        Args:
            record: 数据库记录对象
            metrics: 指标字典
        """
        # 盈利能力指标
        record.roe = metrics.get("roe")
        record.roa = metrics.get("roa")
        record.roic = metrics.get("roic")
        record.gross_margin = metrics.get("gross_margin")
        record.net_margin = metrics.get("net_margin")
        record.operating_margin = metrics.get("operating_margin")

        # 现金流分析指标
        record.fcff = metrics.get("fcff")
        record.fcfe = metrics.get("fcfe")
        record.capex = metrics.get("capex")
        record.cash_conversion_rate = metrics.get("cash_conversion_rate")
        record.ocf_to_sales = metrics.get("ocf_to_sales")

        # 偿债能力指标
        record.debt_ratio = metrics.get("debt_ratio")
        record.current_ratio = metrics.get("current_ratio")
        record.quick_ratio = metrics.get("quick_ratio")
        record.interest_coverage = metrics.get("interest_coverage")

        # 营运能力指标
        record.inventory_turnover = metrics.get("inventory_turnover")
        record.receivables_turnover = metrics.get("receivables_turnover")
        record.asset_turnover = metrics.get("asset_turnover")

        # 成长能力指标
        record.revenue_growth_1y = metrics.get("revenue_growth_1y")
        record.profit_growth_1y = metrics.get("profit_growth_1y")
        record.revenue_cagr_5y = metrics.get("revenue_cagr_5y")
        record.profit_cagr_5y = metrics.get("profit_cagr_5y")
        record.fcff_cagr_5y = metrics.get("fcff_cagr_5y")

        # 估值指标
        record.pe_ratio = metrics.get("pe_ratio")
        record.pb_ratio = metrics.get("pb_ratio")
        record.ps_ratio = metrics.get("ps_ratio")
        record.ev_ebitda = metrics.get("ev_ebitda")
        record.peg_ratio = metrics.get("peg_ratio")

    def calculate_and_save(
        self,
        stock_code: str,
        report_date: str | None = None,
        modules: list[str] | None = None,
        market_data: dict[str, Any] | None = None,
        financial_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """计算并保存财务指标

        Args:
            stock_code: 股票代码
            report_date: 报告日期（可选，默认最新）
            modules: 计算模块列表（可选，默认全部）
            market_data: 市场数据（可选）
            financial_data: 财务数据（可选，用于测试）

        Returns:
            包含 metrics 和 save_result 的字典
        """
        metrics = self.calculate_metrics(
            stock_code=stock_code,
            report_date=report_date,
            modules=modules,
            market_data=market_data,
            financial_data=financial_data,
        )

        save_result = self.save_metrics(stock_code, metrics)

        return {
            "metrics": metrics,
            "saved": save_result,
        }
