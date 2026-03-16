"""测试 BaseMixin"""

from __future__ import annotations
import pytest
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base, Session
from ecox.models.base import BaseMixin


# 创建测试基类
Base = declarative_base()


class TestModel(Base, BaseMixin):
    """测试模型"""
    __tablename__ = 'test_model'

    id = Column(Integer, primary_key=True)


def test_stock_code_validation():
    """测试股票代码验证"""
    model = TestModel()

    # 有效代码
    valid_codes = ['SH600000', 'SZ000001', 'BJ430047', '600000', '000001']
    for code in valid_codes:
        model.stock_code = code
        assert model.stock_code.startswith(('SH', 'SZ', 'BJ'))
        print(f"✓ {code} -> {model.stock_code}")


def test_stock_code_validation_invalid():
    """测试无效代码"""
    model = TestModel()

    with pytest.raises(ValueError, match="Invalid stock code"):
        model.stock_code = "INVALID"


def test_formatted_code_property():
    """测试格式化代码属性"""
    model = TestModel()
    model.stock_code = "600000"
    assert model.formatted_code == "SH600000"


def test_ensure_extra_data():
    """测试 extra_data 管理"""
    model = TestModel()
    model.stock_code = "SH600000"

    # 首次设置
    data1 = {"field1": "value1", "field2": "value2"}
    model.ensure_extra_data(data1)
    assert model.extra_data == data1

    # 追加数据
    data2 = {"field3": "value3"}
    model.ensure_extra_data(data2)
    assert "field1" in model.extra_data
    assert "field3" in model.extra_data


def test_repr():
    """测试字符串表示"""
    model = TestModel()
    model.stock_code = "SH600000"
    assert "SH600000" in repr(model)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
