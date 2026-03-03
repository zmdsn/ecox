"""
统一配置管理模块
从环境变量读取配置，避免硬编码敏感信息
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    from python_dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ValidationConfig:
    """数据验证配置类"""

    # 价格范围配置
    MIN_PRICE = float(os.getenv("VALIDATION_MIN_PRICE", "0.01"))
    MAX_PRICE = float(os.getenv("VALIDATION_MAX_PRICE", "10000"))

    # 成交量配置
    MIN_VOLUME = int(os.getenv("VALIDATION_MIN_VOLUME", "0"))
    MAX_VOLUME = int(os.getenv("VALIDATION_MAX_VOLUME", "1000000000000"))

    # 成交额配置
    MIN_AMOUNT = float(os.getenv("VALIDATION_MIN_AMOUNT", "0"))
    MAX_AMOUNT = float(os.getenv("VALIDATION_MAX_AMOUNT", "100000000000000"))

    # 涨跌幅限制（A股为10%或20%）
    MAX_CHANGE_PCT = float(os.getenv("VALIDATION_MAX_CHANGE_PCT", "20.0"))

    # 价格变化容忍度（用于检查异常波动）
    PRICE_CHANGE_TOLERANCE = float(os.getenv("VALIDATION_PRICE_TOLERANCE", "0.5"))

    # 是否启用严格模式（严格模式会拒绝所有可疑数据）
    STRICT_MODE = os.getenv("VALIDATION_STRICT_MODE", "false").lower() == "true"

    # 是否启用自动清洗（自动修复可修复的数据）
    AUTO_CLEAN = os.getenv("VALIDATION_AUTO_CLEAN", "true").lower() == "true"


class FinancialReportConfig:
    """财报下载配置"""
    REQUEST_INTERVAL = float(os.getenv("FR_REQUEST_INTERVAL", "1.0"))
    BATCH_SIZE = int(os.getenv("FR_BATCH_SIZE", "50"))


class Config:
    """基础配置类"""

    def __init__(self):
        # PostgreSQL 配置
        self.PG_CONFIG = {
            "host": os.getenv("PG_HOST", "localhost"),
            "port": int(os.getenv("PG_PORT", 5432)),
            "user": os.getenv("PG_USER", "zmdsn"),
            "password": os.getenv("PG_PASSWORD", ""),
            "database": os.getenv("PG_DATABASE", "stock"),
            "options": "-c client_encoding=utf8",
        }

        # IoTDB 配置
        self.IOTDB_CONFIG = {
            "host": os.getenv("IOTDB_HOST", "localhost"),
            "port": os.getenv("IOTDB_PORT", "6667"),
            "username": os.getenv("IOTDB_USERNAME", "root"),
            "password": os.getenv("IOTDB_PASSWORD", "root"),
        }

        # API 调用配置
        self.CALL_INTERVAL = float(os.getenv("CALL_INTERVAL", "0.5"))

        # 数据目录
        self.DATA_DIR = BASE_DIR / "data"

        # 验证配置
        self.validation = ValidationConfig()

        # 财报下载配置
        self.financial_report = FinancialReportConfig()


class DevConfig(Config):
    """开发环境配置"""

    DEBUG = True

    def __init__(self):
        super().__init__()
        # 开发环境使用更宽松的验证配置
        self.validation = ValidationConfig()
        self.validation.STRICT_MODE = False
        self.validation.AUTO_CLEAN = True


class ProdConfig(Config):
    """生产环境配置"""

    DEBUG = False

    def __init__(self):
        super().__init__()
        # 生产环境使用默认验证配置
        self.validation = ValidationConfig()


# 根据环境变量选择配置
ENV = os.getenv("ECOX_ENV", "dev")

if ENV == "prod":
    config = ProdConfig()
else:
    config = DevConfig()


# 向后兼容：导出 PG_CONFIG 供旧代码使用
PG_CONFIG = config.PG_CONFIG

# 导出验证配置供使用
VALIDATION_CONFIG = config.validation
