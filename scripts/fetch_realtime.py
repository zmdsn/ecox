#!/usr/bin/env python
"""
启动实时行情采集
使用方法: uv run python scripts/fetch_realtime.py
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecox.data.realtime import create_stock_table, run_job

if __name__ == "__main__":
    create_stock_table()
    run_job()
