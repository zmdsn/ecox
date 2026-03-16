#!/usr/bin/env python
"""
股票数据迁移脚本

功能:
1. 备份现有数据库
2. 统一股票代码格式
3. 补充 extra_data 字段
4. 验证迁移结果
"""

from __future__ import annotations
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ecox.logging_config import setup_logging
from ecox.utils import code_format
from ecox.exceptions import MigrationError
from ecox.database import get_db_session
from ecox.models import StockProfitSheet, StockBalanceSheet, StockCashFlowSheet
from ecox.validators import ProfitSheetValidator

logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""

    def __init__(self, db_url: str | None = None):
        """初始化迁移器"""
        self.db_url = db_url

    def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库

        Args:
            backup_path: 备份文件路径

        Returns:
            是否成功
        """
        logger.info(f"Creating backup at {backup_path}")

        import subprocess

        try:
            # 使用 pg_dump 备份
            result = subprocess.run([
                'pg_dump',
                '-h', 'localhost',
                '-U', 'zmdsn',
                '-d', 'stock',
                '-f', backup_path,
                '--no-owner',
                '--no-acl'
            ], capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                return False

            logger.info("Backup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Backup error: {e}")
            return False

    def migrate_stock_codes(self, dry_run: bool = False) -> dict:
        """
        迁移股票代码格式

        Args:
            dry_run: 是否只模拟运行

        Returns:
            迁移统计
        """
        logger.info("Phase 2: Migrating stock codes...")

        stats = {
            'profit_updated': 0,
            'balance_updated': 0,
            'cashflow_updated': 0,
            'errors': 0
        }

        try:
            with get_db_session() as session:
                # 更新利润表
                profit_records = session.query(StockProfitSheet).all()

                for record in tqdm(profit_records, desc="Migrating profit sheets"):
                    try:
                        old_code = record.stock_code
                        new_code = code_format(old_code)

                        if new_code != old_code:
                            if not dry_run:
                                record.stock_code = new_code

                            stats['profit_updated'] += 1
                            logger.debug(f"{old_code} -> {new_code}")

                    except Exception as e:
                        logger.error(f"Error migrating {record.stock_code}: {e}")
                        stats['errors'] += 1

                if not dry_run:
                    session.commit()

                logger.info(f"Profit sheet migration: {stats['profit_updated']} updated, {stats['errors']} errors")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise MigrationError(f"Stock code migration failed: {e}")

        return stats

    def validate_migrated_data(self, limit: int = 1000) -> list:
        """
        验证迁移后的数据

        Args:
            limit: 验证记录数限制

        Returns:
            验证问题列表
        """
        logger.info("Validating migrated data...")

        issues = []
        validator = ProfitSheetValidator()

        try:
            with get_db_session() as session:
                records = session.query(StockProfitSheet).limit(limit).all()

                for record in tqdm(records, desc="Validating"):
                    data = {
                        'stock_code': record.stock_code,
                        'report_date': str(record.report_date) if record.report_date else None,
                        'total_revenue': float(record.total_revenue) if record.total_revenue else None,
                        'operating_profit': float(record.operating_profit) if record.operating_profit else None,
                        'net_profit': float(record.net_profit) if record.net_profit else None,
                    }

                    validation_issues = validator.validate(data)

                    if validation_issues:
                        issues.append({
                            'stock_code': record.stock_code,
                            'report_date': record.report_date,
                            'issues': [i.to_dict() for i in validation_issues]
                        })

                logger.info(f"Validation completed: {len(issues)} issues found")

        except Exception as e:
            logger.error(f"Validation error: {e}")

        return issues

    def run_full_migration(
        self,
        backup_path: str | None = None,
        dry_run: bool = False
    ) -> dict:
        """
        执行完整迁移流程

        Args:
            backup_path: 备份文件路径
            dry_run: 是否模拟运行

        Returns:
            迁移结果
        """
        logger.info("=" * 60)
        logger.info("Starting data migration")
        if dry_run:
            logger.info("** DRY RUN MODE - No changes will be made **")
        logger.info("=" * 60)

        results = {}

        # Phase 1: 备份
        if backup_path and not dry_run:
            if not self.backup_database(backup_path):
                raise MigrationError("Backup failed, aborting migration")

        # Phase 2: 代码格式统一
        code_stats = self.migrate_stock_codes(dry_run=dry_run)
        results['code_migration'] = code_stats

        # Phase 3: 验证
        validation_issues = self.validate_migrated_data()
        results['validation'] = {
            'total_issues': len(validation_issues),
            'sample_issues': validation_issues[:10]
        }

        logger.info("=" * 60)
        logger.info("Migration completed!")
        logger.info(f"Code migration: {code_stats}")
        logger.info(f"Validation issues: {len(validation_issues)}")
        logger.info("=" * 60)

        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票数据迁移工具')
    parser.add_argument('--backup', type=str, help='备份文件路径')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不修改数据')
    parser.add_argument('--log-level', type=str, default='INFO', help='日志级别')

    args = parser.parse_args()

    # 设置日志
    setup_logging(log_level=args.log_level)

    # 执行迁移
    migrator = DataMigrator()

    try:
        results = migrator.run_full_migration(
            backup_path=args.backup,
            dry_run=args.dry_run
        )

        # 输出结果
        print("\n迁移结果:")
        print(f"  代码迁移: {results['code_migration']}")
        print(f"  验证问题: {results['validation']['total_issues']}")

        if results['validation']['total_issues'] > 0:
            print("\n示例问题:")
            for issue in results['validation']['sample_issues'][:5]:
                print(f"  {issue['stock_code']}: {len(issue['issues'])} issues")

        return 0

    except MigrationError as e:
        logger.error(f"Migration failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
