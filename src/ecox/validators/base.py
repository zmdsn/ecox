"""验证器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from .result import ValidationResult


class DataValidator(ABC):
    """数据验证器基类"""

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证单条数据

        Args:
            data: 待验证的数据字典

        Returns:
            ValidationResult: 验证结果
        """
        pass

    def validate_batch(self, data_list: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        批量验证数据

        Args:
            data_list: 待验证的数据列表

        Returns:
            List[ValidationResult]: 验证结果列表
        """
        return [self.validate(data) for data in data_list]

    def _get_float(self, data: Dict, key: str, default: float = 0.0) -> float:
        """安全获取浮点数"""
        value = data.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
