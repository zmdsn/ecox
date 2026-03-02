"""验证结果数据类"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date


@dataclass
class ValidationResult:
    """数据验证结果"""

    is_valid: bool
    """是否验证通过"""

    errors: List[str] = field(default_factory=list)
    """错误列表（致命问题，数据不可用）"""

    warnings: List[str] = field(default_factory=list)
    """警告列表（可修复的异常）"""

    cleaned_data: Optional[Dict[str, Any]] = None
    """清洗后的数据，如果数据可修复"""

    alert_level: str = "INFO"
    """告警级别: INFO, WARNING, ERROR"""

    def add_error(self, message: str):
        """添加错误"""
        self.errors.append(message)
        self.is_valid = False
        self.alert_level = "ERROR"

    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
        if self.alert_level != "ERROR":
            self.alert_level = "WARNING"

    def has_issues(self) -> bool:
        """是否有任何问题"""
        return bool(self.errors or self.warnings)
