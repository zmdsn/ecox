"""模型数据验证器"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationSeverity(Enum):
    """验证严重级别"""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """验证问题"""
    field: str
    message: str
    severity: ValidationSeverity
    value: Any = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "value": self.value
        }


class ModelValidator:
    """模型验证器基类"""

    # 必填字段
    REQUIRED_FIELDS = ['stock_code', 'report_date']

    # 数值字段
    NUMERIC_FIELDS = ['total_revenue', 'operating_profit', 'net_profit',
                      'total_assets', 'total_liabilities']

    def validate(self, data: dict[str, Any]) -> list[ValidationIssue]:
        """
        验证数据，返回问题列表

        Args:
            data: 待验证的数据字典

        Returns:
            验证问题列表
        """
        issues = []

        issues.extend(self._validate_required_fields(data))
        issues.extend(self._validate_types(data))
        issues.extend(self._validate_business_rules(data))
        issues.extend(self._validate_cross_field_relations(data))

        return issues

    def _validate_required_fields(self, data: dict[str, Any]) -> list[ValidationIssue]:
        """验证必填字段"""
        issues = []

        for field in self.REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                issues.append(ValidationIssue(
                    field=field,
                    message="Required field missing",
                    severity=ValidationSeverity.ERROR
                ))

        return issues

    def _validate_types(self, data: dict[str, Any]) -> list[ValidationIssue]:
        """验证数据类型"""
        issues = []

        for field in self.NUMERIC_FIELDS:
            if field in data and data[field] is not None:
                if not isinstance(data[field], (int, float)):
                    issues.append(ValidationIssue(
                        field=field,
                        message=f"Must be numeric, got {type(data[field]).__name__}",
                        severity=ValidationSeverity.ERROR,
                        value=data[field]
                    ))

        return issues

    def _validate_business_rules(self, data: dict[str, Any]) -> list[ValidationIssue]:
        """业务规则验证"""
        issues = []

        # 规则1: 收入不应为负
        if data.get('total_revenue'):
            revenue = data['total_revenue']
            try:
                revenue_val = float(revenue)
                if revenue_val < 0:
                    issues.append(ValidationIssue(
                        field='total_revenue',
                        message=f"Revenue cannot be negative: {revenue_val}",
                        severity=ValidationSeverity.ERROR,
                        value=revenue_val
                    ))
            except (ValueError, TypeError):
                pass

        # 规则2: 净利润不应超过营收的10倍（异常检测）
        if data.get('total_revenue') and data.get('net_profit'):
            try:
                revenue = float(data['total_revenue'])
                profit = float(data['net_profit'])

                if revenue > 0 and abs(profit) > abs(revenue) * 10:
                    issues.append(ValidationIssue(
                        field='net_profit',
                        message=f"Net profit anomaly: {profit:.2f} exceeds 10x revenue: {revenue:.2f}",
                        severity=ValidationSeverity.WARNING,
                        value=profit
                    ))
            except (ValueError, TypeError):
                pass

        return issues

    def _validate_cross_field_relations(self, data: dict[str, Any]) -> list[ValidationIssue]:
        """勾稽关系检查"""
        issues = []

        # 检查营业利润和净利润的一致性
        if data.get('operating_profit') and data.get('net_profit'):
            try:
                operating = float(data['operating_profit'])
                net = float(data['net_profit'])

                # 如果营业利润为正，净利润不应为负（特殊情况除外）
                if operating > 0 and net < 0:
                    issues.append(ValidationIssue(
                        field='net_profit',
                        message=f"Sign inconsistency: operating profit is positive ({operating}) but net profit is negative ({net})",
                        severity=ValidationSeverity.WARNING
                    ))
            except (ValueError, TypeError):
                pass

        return issues


class ProfitSheetValidator(ModelValidator):
    """利润表验证器"""

    REQUIRED_FIELDS = ['stock_code', 'report_date', 'total_revenue']

    def _validate_business_rules(self, data: dict[str, Any]) -> list[ValidationIssue]:
        """利润表特定规则"""
        issues = super()._validate_business_rules(data)

        # 计算毛利率并检查合理性
        if data.get('total_revenue') and data.get('operating_cost'):
            try:
                revenue = float(data['total_revenue'])
                cost = float(data['operating_cost'])

                if revenue > 0:
                    gross_margin = (revenue - cost) / revenue * 100

                    if gross_margin < -50 or gross_margin > 100:
                        issues.append(ValidationIssue(
                            field='total_revenue',
                            message=f"Gross profit margin anomaly: {gross_margin:.2f}%",
                            severity=ValidationSeverity.WARNING,
                            value=gross_margin
                        ))
            except (ValueError, TypeError):
                pass

        return issues


class BalanceSheetValidator(ModelValidator):
    """资产负债表验证器"""

    REQUIRED_FIELDS = ['stock_code', 'report_date', 'total_assets']

    def _validate_business_rules(self, data: dict[str, Any]) -> list[ValidationIssue]:
        """资产负债表特定规则"""
        issues = super()._validate_business_rules(data)

        # 资产负债率应在合理范围内
        if data.get('total_assets') and data.get('total_liabilities'):
            try:
                assets = float(data['total_assets'])
                liabilities = float(data['total_liabilities'])

                if assets > 0:
                    debt_ratio = (liabilities / assets) * 100

                    if debt_ratio > 100:
                        issues.append(ValidationIssue(
                            field='total_liabilities',
                            message=f"Debt ratio exceeds 100%: {debt_ratio:.2f}%",
                            severity=ValidationSeverity.WARNING,
                            value=debt_ratio
                        ))
            except (ValueError, TypeError):
                pass

        return issues
