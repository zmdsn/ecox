#!/usr/bin/env python
"""
启动日线数据更新
使用方法: uv run python scripts/fetch_daily.py
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecox.data.daily import main_daily_update

if __name__ == "__main__":
    # 日常增量更新（推荐）
    main_daily_update()

    # 首次全量拉取（谨慎使用）
    # initial_full_load()
