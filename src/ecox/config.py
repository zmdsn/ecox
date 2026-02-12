"""
统一配置管理模块
从环境变量读取配置，避免硬编码敏感信息
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Config:
    """基础配置类"""

    # PostgreSQL 配置
    PG_CONFIG = {
        "host": os.getenv("PG_HOST", "localhost"),
        "port": int(os.getenv("PG_PORT", 5432)),
        "user": os.getenv("PG_USER", "zmdsn"),
        "password": os.getenv("PG_PASSWORD", ""),
        "database": os.getenv("PG_DATABASE", "stock"),
        "options": "-c client_encoding=utf8",
    }

    # IoTDB 配置
    IOTDB_CONFIG = {
        "host": os.getenv("IOTDB_HOST", "localhost"),
        "port": os.getenv("IOTDB_PORT", "6667"),
        "username": os.getenv("IOTDB_USERNAME", "root"),
        "password": os.getenv("IOTDB_PASSWORD", "root"),
    }

    # API 调用配置
    CALL_INTERVAL = float(os.getenv("CALL_INTERVAL", "0.5"))

    # 数据目录
    DATA_DIR = BASE_DIR / "data"


class DevConfig(Config):
    """开发环境配置"""

    DEBUG = True


class ProdConfig(Config):
    """生产环境配置"""

    DEBUG = False


# 根据环境变量选择配置
ENV = os.getenv("ECOX_ENV", "dev")

if ENV == "prod":
    config = ProdConfig()
else:
    config = DevConfig()


# 向后兼容：导出 PG_CONFIG 供旧代码使用
PG_CONFIG = config.PG_CONFIG
