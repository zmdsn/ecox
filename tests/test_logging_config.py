"""测试日志配置"""

import logging
import pytest
from pathlib import Path
from ecox.logging_config import setup_logging, get_logger


def test_setup_logging_default():
    """测试默认日志配置"""
    logger = setup_logging(log_level="INFO", enable_file=False)
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_get_logger():
    """测试获取日志器"""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


def test_log_file_creation(tmp_path):
    """测试日志文件创建"""
    log_dir = tmp_path / "logs"
    logger = setup_logging(
        log_level="DEBUG",
        log_dir=str(log_dir),
        enable_console=False,
        enable_file=True
    )

    # 写入日志
    test_logger = get_logger("test")
    test_logger.info("Test message")

    # 检查文件是否创建
    log_files = list(Path(log_dir).glob("ecox_*.log"))
    assert len(log_files) > 0

    # 检查日志内容
    log_content = log_files[0].read_text()
    assert "Test message" in log_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
