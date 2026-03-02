"""组合验证器"""
from typing import List, Dict, Any

from .base import DataValidator
from .result import ValidationResult


class CompositeValidator(DataValidator):
    """组合验证器

    按顺序执行多个验证器，收集所有错误和警告
    """

    def __init__(self, validators: List[DataValidator]):
        """
        初始化组合验证器

        Args:
            validators: 验证器列表
        """
        self.validators = validators

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        执行所有验证器

        Args:
            data: 待验证的数据

        Returns:
            ValidationResult: 合并后的验证结果
        """
        combined_result = ValidationResult(is_valid=True)

        for validator in self.validators:
            result = validator.validate(data)

            # 合并错误
            for error in result.errors:
                combined_result.add_error(error)

            # 合并警告
            for warning in result.warnings:
                combined_result.add_warning(warning)

            # 如果有清洗后的数据，使用它
            if result.cleaned_data is not None:
                combined_result.cleaned_data = result.cleaned_data

        return combined_result

    def add_validator(self, validator: DataValidator):
        """添加验证器"""
        self.validators.append(validator)
