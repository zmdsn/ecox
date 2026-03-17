#!/usr/bin/env python3
"""
批量同步所有股票数据到 stock_price 表
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
import subprocess
from datetime import datetime

from ecox.database import get_db_session
from ecox import models

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def get_all_stocks_with_data():
    """获取所有有日线数据的股票代码"""
    with get_db_session() as session:
        result = session.query(
            models.StockDailyData.stock_code
        ).distinct().all()
        return [r[0] for r in result]


def get_synced_stocks():
    """获取已同步的股票代码"""
    with get_db_session() as session:
        result = session.query(
            models.StockPrice.stock_code
        ).distinct().all()
        return set([r[0] for r in result])


def batch_sync(stock_codes, batch_size=20):
    """
    批量同步股票

    Args:
        stock_codes: 股票代码列表
        batch_size: 每批处理的数量
    """
    synced = get_synced_stocks()
    to_sync = [c for c in stock_codes if c not in synced]

    logger.info(f"需要同步的股票数量: {len(to_sync)}")
    logger.info(f"已同步的股票数量: {len(synced)}")

    total = len(to_sync)
    for i in range(0, total, batch_size):
        batch = to_sync[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        logger.info(f"处理批次 {batch_num}/{total_batches}: {batch}")

        cmd = ["uv", "run", "python", "sync_prices.py", *batch, "--sync", "--days", "365"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"批次 {batch_num} 失败: {result.stderr}")

        # 每批次后检查进度
        synced_now = get_synced_stocks()
        logger.info(f"当前进度: {len(synced_now)}/5467 ({len(synced_now)/5467*100:.1f}%)")


def main():
    """主函数"""
    logger.info("开始批量同步所有股票数据...")

    # 获取所有股票
    all_stocks = get_all_stocks_with_data()
    logger.info(f"stock_daily_data 表中共有 {len(all_stocks)} 只股票的数据")

    # 批量同步
    batch_sync(all_stocks, batch_size=20)

    logger.info("批量同步完成!")


if __name__ == "__main__":
    main()
