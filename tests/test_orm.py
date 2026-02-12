"""
ORM 模块测试
测试 SQLAlchemy ORM 模型和仓库层
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime, date
from ecox.database import init_db, get_db_session
from ecox import models


def test_database_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    try:
        db = init_db()
        engine = db.get_engine()
        print(f"✓ 数据库连接成功: {engine.url}")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False


def test_create_tables():
    """测试表结构创建"""
    print("\n测试表结构创建...")
    try:
        db = init_db()
        db.create_all()
        print("✓ 表结构创建成功")
        return True
    except Exception as e:
        print(f"✗ 表结构创建失败: {e}")
        return False


def test_stock_basic_model():
    """测试股票基础信息模型"""
    print("\n测试 StockBasic 模型...")

    try:
        import time
        # 使用时间戳生成唯一的测试代码
        test_code = f"99{int(time.time()) % 1000000:06d}"
        test_name = f"测试股票{test_code}"

        with get_db_session() as session:
            # 创建测试数据
            stock = models.StockBasic(
                stock_code=test_code,
                stock_name=test_name,
                industry="银行",
                list_date=date(2020, 1, 1),
            )
            session.add(stock)
            session.commit()
            session.refresh(stock)

            print(f"✓ 创建股票成功: {stock.stock_code} {stock.stock_name}")

            # 查询测试
            queried = session.query(models.StockBasic).filter(
                models.StockBasic.stock_code == test_code
            ).first()

            if queried:
                print(f"✓ 查询股票成功: {queried.stock_name}")
            else:
                print("✗ 查询股票失败")
                return False

            # 清理测试数据
            session.delete(stock)
            session.commit()

            return True

    except Exception as e:
        print(f"✗ StockBasic 模型测试失败: {e}")
        return False


def test_stock_daily_data_model():
    """测试日线数据模型"""
    print("\n测试 StockDailyData 模型...")

    try:
        with get_db_session() as session:
            # 创建测试数据
            daily = models.StockDailyData(
                stock_code="600000",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=10.5,
                high=10.8,
                low=9.8,
                volume=1000000,
                amount=10500000,
                adjust_flag="qfq",
            )
            session.add(daily)
            session.commit()

            print(f"✓ 创建日线数据成功: {daily.stock_code} {daily.trade_date}")

            # 清理测试数据
            session.delete(daily)
            session.commit()

            return True

    except Exception as e:
        print(f"✗ StockDailyData 模型测试失败: {e}")
        return False


def test_stock_repository():
    """测试股票仓库"""
    print("\n测试 StockRepository...")

    try:
        from ecox.repositories import StockRepository

        repo = StockRepository()

        # 测试 get_or_create
        stock = repo.get_or_create("600001", "测试股票2")
        print(f"✓ get_or_create 成功: {stock.stock_code} {stock.stock_name}")

        # 测试 get_by_code
        queried = repo.get_by_code("600001")
        if queried:
            print(f"✓ get_by_code 成功: {queried.stock_name}")
        else:
            print("✗ get_by_code 失败")
            return False

        return True

    except Exception as e:
        print(f"✗ StockRepository 测试失败: {e}")
        return False


def test_stock_service():
    """测试股票服务"""
    print("\n测试 StockService...")

    try:
        from ecox.services import StockService

        service = StockService()

        # 测试 save_stock_info
        info = service.save_stock_info(
            stock_code="600002",
            stock_name="测试股票3",
            industry="银行",
        )
        print(f"✓ save_stock_info 成功: {info}")

        # 测试 get_stock_info
        queried = service.get_stock_info("600002")
        if queried:
            print(f"✓ get_stock_info 成功: {queried['stock_name']}")
        else:
            print("✗ get_stock_info 失败")
            return False

        # 测试 get_stock_list
        stock_list = service.get_stock_list()
        print(f"✓ get_stock_list 成功: 共 {len(stock_list)} 只股票")

        return True

    except Exception as e:
        print(f"✗ StockService 测试失败: {e}")
        return False


def test_data_collection_service():
    """测试数据采集服务"""
    print("\n测试 DataCollectionService...")

    try:
        from ecox.services import DataCollectionService

        service = DataCollectionService()

        # 测试 save_realtime_data
        test_data = [{
            "stock_code": "600003",
            "stock_name": "测试股票4",
            "latest_price": 10.5,
            "price_change": 0.5,
            "price_change_rate": 5.0,
            "volume": 1000000,
            "turnover": 10500000,
            "high_price": 10.8,
            "low_price": 10.2,
            "open_price": 10.3,
            "pre_close_price": 10.0,
        }]

        result = service.save_realtime_data(test_data)
        print(f"✓ save_realtime_data 成功: {result}")

        # 测试 get_latest_update_log
        log = service.get_latest_update_log()
        print(f"✓ get_latest_update_log: {log}")

        return True

    except Exception as e:
        print(f"✗ DataCollectionService 测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始 ORM 模块测试")
    print("=" * 60)

    results = []

    results.append(("数据库连接", test_database_connection()))
    results.append(("表结构创建", test_create_tables()))
    results.append(("StockBasic 模型", test_stock_basic_model()))
    results.append(("StockDailyData 模型", test_stock_daily_data_model()))
    results.append(("StockRepository", test_stock_repository()))
    results.append(("StockService", test_stock_service()))
    results.append(("DataCollectionService", test_data_collection_service()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n总计: {passed}/{total} 测试通过")

    return all(r for _, r in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
