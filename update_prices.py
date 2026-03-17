#!/usr/bin/env python3
"""
股票价格每日更新脚本
统一的增量更新逻辑，支持断点续传
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ecox.services.daily_update_service import DailyUpdateService

if __name__ == "__main__":
    service = DailyUpdateService()
    service.update_today()
