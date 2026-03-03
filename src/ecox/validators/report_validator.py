"""财报验证器"""
import math
from typing import Any

from .result import ValidationResult


class ReportValidator:
    """财报数据验证器"""

    def __init__(self):
        pass

    def validate_profit_sheet(self, data: dict[str, Any]) -> ValidationResult:
        """验证利润表数据 - 核心字段非负、NaN检查"""
        result = ValidationResult(is_valid=True)

        core_fields = {
            "total_revenue": "营业总收入",
            "operating_profit": "营业利润",
            "net_profit": "净利润",
        }

        for field, name in core_fields.items():
            value = data.get(field)
            if value is None:
                continue
            if isinstance(value, float) and math.isnan(value):
                result.add_error(f"{name} 为 NaN")
                continue
            try:
                num_value = float(value)
                if num_value < 0:
                    result.add_error(f"{name} 为负值: {num_value}")
            except (ValueError, TypeError):
                result.add_error(f"{name} 格式错误: {value}")
        return result

    def validate_balance_sheet(self, data: dict[str, Any]) -> ValidationResult:
        """验证资产负债表数据 - 非负检查 + 勾稽关系检查"""
        result = ValidationResult(is_valid=True)

        core_fields = {
            "total_assets": "总资产",
            "total_liabilities": "总负债",
            "owner_equity": "所有者权益",
        }

        for field, name in core_fields.items():
            value = data.get(field)
            if value is None:
                continue
            if isinstance(value, float) and math.isnan(value):
                result.add_error(f"{name} 为 NaN")
                continue
            try:
                num_value = float(value)
                if num_value < 0:
                    result.add_error(f"{name} 为负值: {num_value}")
            except (ValueError, TypeError):
                result.add_error(f"{name} 格式错误: {value}")

        # 勾稽关系检查
        assets = data.get("total_assets")
        liabilities = data.get("total_liabilities")
        equity = data.get("owner_equity")

        if all(v is not None for v in [assets, liabilities, equity]):
            try:
                assets_val = float(assets)
                liabilities_val = float(liabilities)
                equity_val = float(equity)

                if not any(math.isnan(v) for v in [assets_val, liabilities_val, equity_val]):
                    calculated = liabilities_val + equity_val
                    tolerance = max(abs(assets_val) * 0.01, 1000)
                    if abs(assets_val - calculated) > tolerance:
                        result.add_warning(
                            f"勾稽关系不匹配: 资产({assets_val:.0f}) != "
                            f"负债({liabilities_val:.0f}) + 权益({equity_val:.0f})"
                        )
            except (ValueError, TypeError):
                pass
        return result

    def validate_cash_flow_sheet(self, data: dict[str, Any]) -> ValidationResult:
        """验证现金流量表数据 - NaN检查（值可以为负）"""
        result = ValidationResult(is_valid=True)

        core_fields = {
            "operating_cash_flow": "经营活动现金流",
            "investing_cash_flow": "投资活动现金流",
            "financing_cash_flow": "筹资活动现金流",
        }

        for field, name in core_fields.items():
            value = data.get(field)
            if value is None:
                continue
            if isinstance(value, float) and math.isnan(value):
                result.add_error(f"{name} 为 NaN")
            elif not isinstance(value, (int, float)):
                result.add_error(f"{name} 格式错误: {value}")
        return result
