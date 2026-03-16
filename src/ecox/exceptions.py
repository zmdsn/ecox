"""Ecox 自定义异常类"""

class EcoxException(Exception):
    """Ecox 基础异常类"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class StockCodeError(EcoxException):
    """股票代码格式错误"""
    pass


class DataValidationError(EcoxException):
    """数据验证错误"""

    def __init__(self, message: str, issues: list = None):
        super().__init__(message)
        self.issues = issues or []

    def __str__(self):
        if self.issues:
            issues_str = "; ".join([f"{i.field}: {i.message}" for i in self.issues[:5]])
            return f"{self.message} - Issues: {issues_str}"
        return self.message


class DataIntegrityError(EcoxException):
    """数据完整性错误"""
    pass


class MigrationError(EcoxException):
    """数据迁移错误"""
    pass


class ExternalDataSourceError(EcoxException):
    """外部数据源错误（如 akshare）"""
    pass
