"""数据模型基类"""

from __future__ import annotations
import re
from sqlalchemy import Column, String
from sqlalchemy.orm import declared_attr, validates
from ecox.utils import code_format


class BaseMixin:
    """
    所有财务报表模型的混合基类

    提供:
    - 自动股票代码格式化
    - 代码验证
    - extra_data 管理
    """

    @declared_attr
    def stock_code(cls):
        """声明股票代码列"""
        return Column(String(10), nullable=False, index=True, comment="股票代码（带交易所前缀）")

    @property
    def formatted_code(self) -> str:
        """获取格式化的代码（带前缀）"""
        return code_format(self.stock_code)

    def ensure_extra_data(self, raw_data: dict) -> None:
        """
        确保 extra_data 包含完整的原始数据

        Args:
            raw_data: 原始数据字典
        """
        if not hasattr(self, 'extra_data') or self.extra_data is None:
            self.extra_data = raw_data
        else:
            # 合并缺失的字段
            for key, value in raw_data.items():
                if key not in self.extra_data:
                    self.extra_data[key] = value

    @validates('stock_code')
    def validate_stock_code(self, key, value):
        """
        验证股票代码格式

        Args:
            key: 字段名
            value: 股票代码值

        Returns:
            格式化后的股票代码

        Raises:
            ValueError: 代码格式无效
        """
        if value is None:
            return None

        # 格式化代码
        formatted = code_format(str(value))

        # 验证格式
        if not self._is_valid_code(formatted):
            raise ValueError(f"Invalid stock code format: {value}. Expected format: SH/SZ/BJ + 6 digits.")

        return formatted

    def _is_valid_code(self, code: str) -> bool:
        """
        检查代码是否有效

        Args:
            code: 股票代码

        Returns:
            是否有效
        """
        return bool(re.match(r'^(SH|SZ|BJ)\d{6}$', code))

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__} {self.stock_code}>"
