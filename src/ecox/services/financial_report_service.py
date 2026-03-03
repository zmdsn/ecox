"""财务报表下载服务"""
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import akshare as ak

from ..database import get_db_session
from .. import models
from ..validators.report_validator import ReportValidator
from .alert_service import AlertService
from ..config import config

logger = logging.getLogger(__name__)


class FinancialReportService:
    """财务报表下载服务"""

    def __init__(self):
        self.validator = ReportValidator()
        self.alert_service = AlertService()

    def _get_stock_list(self) -> List[str]:
        """获取所有股票代码"""
        with get_db_session() as session:
            stocks = session.query(models.StockBasic.stock_code).all()
            return [s.stock_code for s in stocks]

    def _code_format(self, code: str) -> str:
        """格式化股票代码为 akshare 格式"""
        code = code.replace("SH", "").replace("SZ", "")
        if code.startswith("6"):
            return f"SH{code}"
        else:
            return f"SZ{code}"

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def fetch_profit_sheet(self, stock_code: str) -> List[Dict]:
        """下载利润表数据"""
        try:
            symbol = self._code_format(stock_code)
            df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
            if df.empty:
                logger.warning(f"股票 {stock_code} 无利润表数据")
                return []

            data_list = []
            for _, row in df.iterrows():
                item = {
                    "stock_code": stock_code,
                    "stock_name": row.get("股票简称", ""),
                    "report_date": str(row.get("报告日期", "")),
                    "report_type": str(row.get("报告类型", "")),
                    "total_revenue": self._safe_float(row.get("营业总收入")),
                    "operating_profit": self._safe_float(row.get("营业利润")),
                    "net_profit": self._safe_float(row.get("净利润")),
                    "basic_eps": self._safe_float(row.get("基本每股收益")),
                }
                extra_data = {}
                for col in df.columns:
                    if col not in ["股票简称", "报告日期", "报告类型"]:
                        extra_data[col] = row.get(col)
                item["extra_data"] = extra_data
                data_list.append(item)

            logger.info(f"股票 {stock_code} 下载利润表 {len(data_list)} 条记录")
            return data_list
        except Exception as e:
            logger.error(f"下载 {stock_code} 利润表失败: {e}")
            return []

    def fetch_balance_sheet(self, stock_code: str) -> List[Dict]:
        """下载资产负债表数据"""
        try:
            symbol = self._code_format(stock_code)
            df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
            if df.empty:
                return []

            data_list = []
            for _, row in df.iterrows():
                item = {
                    "stock_code": stock_code,
                    "stock_name": row.get("股票简称", ""),
                    "report_date": str(row.get("报告日期", "")),
                    "report_type": str(row.get("报告类型", "")),
                    "total_assets": self._safe_float(row.get("资产总计")),
                    "total_liabilities": self._safe_float(row.get("负债合计")),
                    "owner_equity": self._safe_float(row.get("所有者权益合计")),
                }
                extra_data = {}
                for col in df.columns:
                    if col not in ["股票简称", "报告日期", "报告类型"]:
                        extra_data[col] = row.get(col)
                item["extra_data"] = extra_data
                data_list.append(item)
            return data_list
        except Exception as e:
            logger.error(f"下载 {stock_code} 资产负债表失败: {e}")
            return []

    def fetch_cash_flow_sheet(self, stock_code: str) -> List[Dict]:
        """下载现金流量表数据"""
        try:
            symbol = self._code_format(stock_code)
            df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
            if df.empty:
                return []

            data_list = []
            for _, row in df.iterrows():
                item = {
                    "stock_code": stock_code,
                    "stock_name": row.get("股票简称", ""),
                    "report_date": str(row.get("报告日期", "")),
                    "report_type": str(row.get("报告类型", "")),
                    "operating_cash_flow": self._safe_float(row.get("经营活动产生的现金流量净额")),
                    "investing_cash_flow": self._safe_float(row.get("投资活动产生的现金流量净额")),
                    "financing_cash_flow": self._safe_float(row.get("筹资活动产生的现金流量净额")),
                }
                extra_data = {}
                for col in df.columns:
                    if col not in ["股票简称", "报告日期", "报告类型"]:
                        extra_data[col] = row.get(col)
                item["extra_data"] = extra_data
                data_list.append(item)
            return data_list
        except Exception as e:
            logger.error(f"下载 {stock_code} 现金流量表失败: {e}")
            return []

    def save_profit_sheet(self, stock_code: str, data_list: List[Dict]) -> Dict[str, int]:
        """保存利润表数据（带验证）"""
        saved_count = 0
        skipped_count = 0
        failed_count = 0

        with get_db_session() as session:
            for data in data_list:
                try:
                    result = self.validator.validate_profit_sheet(data)
                    if not result.is_valid:
                        self.alert_service.create_alert(
                            stock_code=stock_code,
                            stock_name=data.get("stock_name"),
                            alert_type="profit_sheet_validation_failed",
                            result=result,
                            raw_data=data,
                        )
                        failed_count += 1
                        continue

                    existing = session.query(models.StockProfitSheet).filter(
                        models.StockProfitSheet.stock_code == stock_code,
                        models.StockProfitSheet.report_date == data.get("report_date")
                    ).first()

                    if existing:
                        existing.total_revenue = data.get("total_revenue")
                        existing.operating_profit = data.get("operating_profit")
                        existing.net_profit = data.get("net_profit")
                        existing.basic_eps = data.get("basic_eps")
                        existing.extra_data = data.get("extra_data")
                        existing.update_time = datetime.now()
                        skipped_count += 1
                    else:
                        record = models.StockProfitSheet(
                            stock_code=stock_code,
                            stock_name=data.get("stock_name", ""),
                            report_date=data.get("report_date"),
                            report_type=data.get("report_type"),
                            total_revenue=data.get("total_revenue"),
                            operating_profit=data.get("operating_profit"),
                            net_profit=data.get("net_profit"),
                            basic_eps=data.get("basic_eps"),
                            extra_data=data.get("extra_data"),
                        )
                        session.add(record)
                        saved_count += 1
                except Exception as e:
                    logger.error(f"保存 {stock_code} 利润表数据失败: {e}")
                    failed_count += 1
            session.commit()

        return {"saved": saved_count, "skipped": skipped_count, "failed": failed_count, "total": len(data_list)}

    def save_balance_sheet(self, stock_code: str, data_list: List[Dict]) -> Dict[str, int]:
        """保存资产负债表数据（类似逻辑）"""
        saved_count = 0
        skipped_count = 0
        failed_count = 0

        with get_db_session() as session:
            for data in data_list:
                try:
                    result = self.validator.validate_balance_sheet(data)
                    if not result.is_valid:
                        failed_count += 1
                        continue

                    existing = session.query(models.StockBalanceSheet).filter(
                        models.StockBalanceSheet.stock_code == stock_code,
                        models.StockBalanceSheet.report_date == data.get("report_date")
                    ).first()

                    if existing:
                        existing.total_assets = data.get("total_assets")
                        existing.total_liabilities = data.get("total_liabilities")
                        existing.owner_equity = data.get("owner_equity")
                        existing.extra_data = data.get("extra_data")
                        existing.update_time = datetime.now()
                        skipped_count += 1
                    else:
                        record = models.StockBalanceSheet(
                            stock_code=stock_code,
                            stock_name=data.get("stock_name", ""),
                            report_date=data.get("report_date"),
                            report_type=data.get("report_type"),
                            total_assets=data.get("total_assets"),
                            total_liabilities=data.get("total_liabilities"),
                            owner_equity=data.get("owner_equity"),
                            extra_data=data.get("extra_data"),
                        )
                        session.add(record)
                        saved_count += 1
                except Exception as e:
                    logger.error(f"保存 {stock_code} 资产负债表数据失败: {e}")
                    failed_count += 1
            session.commit()

        return {"saved": saved_count, "skipped": skipped_count, "failed": failed_count, "total": len(data_list)}

    def save_cash_flow_sheet(self, stock_code: str, data_list: List[Dict]) -> Dict[str, int]:
        """保存现金流量表数据（类似逻辑）"""
        saved_count = 0
        skipped_count = 0
        failed_count = 0

        with get_db_session() as session:
            for data in data_list:
                try:
                    result = self.validator.validate_cash_flow_sheet(data)
                    if not result.is_valid:
                        failed_count += 1
                        continue

                    existing = session.query(models.StockCashFlowSheet).filter(
                        models.StockCashFlowSheet.stock_code == stock_code,
                        models.StockCashFlowSheet.report_date == data.get("report_date")
                    ).first()

                    if existing:
                        existing.operating_cash_flow = data.get("operating_cash_flow")
                        existing.investing_cash_flow = data.get("investing_cash_flow")
                        existing.financing_cash_flow = data.get("financing_cash_flow")
                        existing.extra_data = data.get("extra_data")
                        existing.update_time = datetime.now()
                        skipped_count += 1
                    else:
                        record = models.StockCashFlowSheet(
                            stock_code=stock_code,
                            stock_name=data.get("stock_name", ""),
                            report_date=data.get("report_date"),
                            report_type=data.get("report_type"),
                            operating_cash_flow=data.get("operating_cash_flow"),
                            investing_cash_flow=data.get("investing_cash_flow"),
                            financing_cash_flow=data.get("financing_cash_flow"),
                            extra_data=data.get("extra_data"),
                        )
                        session.add(record)
                        saved_count += 1
                except Exception as e:
                    logger.error(f"保存 {stock_code} 现金流量表数据失败: {e}")
                    failed_count += 1
            session.commit()

        return {"saved": saved_count, "skipped": skipped_count, "failed": failed_count, "total": len(data_list)}

    def fetch_all_reports(self, stock_code: str) -> Dict[str, List[Dict]]:
        """下载单股票的所有报表"""
        logger.info(f"开始下载 {stock_code} 的所有财报")
        result = {"profit": [], "balance": [], "cash_flow": []}

        profit_data = self.fetch_profit_sheet(stock_code)
        if profit_data:
            self.save_profit_sheet(stock_code, profit_data)
            result["profit"] = profit_data
        time.sleep(config.financial_report.REQUEST_INTERVAL)

        balance_data = self.fetch_balance_sheet(stock_code)
        if balance_data:
            self.save_balance_sheet(stock_code, balance_data)
            result["balance"] = balance_data
        time.sleep(config.financial_report.REQUEST_INTERVAL)

        cash_flow_data = self.fetch_cash_flow_sheet(stock_code)
        if cash_flow_data:
            self.save_cash_flow_sheet(stock_code, cash_flow_data)
            result["cash_flow"] = cash_flow_data

        return result

    def batch_fetch_all_stocks(self, stock_codes: Optional[List[str]] = None, limit: Optional[int] = None) -> Dict[str, int]:
        """批量下载所有股票的财报"""
        if not stock_codes:
            stock_codes = self._get_stock_list()
        if limit:
            stock_codes = stock_codes[:limit]

        logger.info(f"开始批量下载 {len(stock_codes)} 只股票的财报")
        total_profit = total_balance = total_cash_flow = 0
        failed = []

        for i, code in enumerate(stock_codes):
            try:
                logger.info(f"处理 {i+1}/{len(stock_codes)}: {code}")
                result = self.fetch_all_reports(code)
                total_profit += len(result.get("profit", []))
                total_balance += len(result.get("balance", []))
                total_cash_flow += len(result.get("cash_flow", []))
                if (i + 1) % 50 == 0:
                    logger.info(f"进度: {i+1}/{len(stock_codes)}, 利润表: {total_profit}, 资产负债表: {total_balance}, 现金流量表: {total_cash_flow}")
            except Exception as e:
                logger.error(f"处理 {code} 时出错: {e}")
                failed.append(code)

        logger.info("=" * 60)
        logger.info("批量下载完成!")
        logger.info(f"总计: 利润表 {total_profit} 条, 资产负债表 {total_balance} 条, 现金流量表 {total_cash_flow} 条")
        if failed:
            logger.info(f"失败股票（前20个）: {failed[:20]}")

        return {"profit_count": total_profit, "balance_count": total_balance, "cash_flow_count": total_cash_flow, "failed_count": len(failed)}
