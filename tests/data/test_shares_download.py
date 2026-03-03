"""
测试股票基础信息下载功能
测试模块: src/ecox/data/shares.py
"""
import pytest
import pandas as pd
from src.ecox.data.shares import get_stock_basic_raw, supplement_stock_detail
from src.ecox.models import StockBasic


class TestGetStockBasicRaw:
    """测试 get_stock_basic_raw() 函数"""

    def test_returns_dataframe(self):
        """验证返回类型为 DataFrame"""
        df = get_stock_basic_raw()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        """验证必需列存在"""
        df = get_stock_basic_raw()
        required_columns = ["stock_code", "stock_name"]
        for col in required_columns:
            assert col in df.columns, f"缺少列: {col}"

    def test_data_not_empty(self):
        """验证数据非空"""
        df = get_stock_basic_raw()
        assert len(df) > 0, "返回数据为空"

    def test_stock_code_format(self):
        """验证股票代码格式（6位数字）"""
        df = get_stock_basic_raw()
        # 所有代码应该是6位数字
        assert df["stock_code"].str.match(r"^\d{6}$").all(), "股票代码格式错误"

    def test_no_duplicates(self):
        """验证无重复代码"""
        df = get_stock_basic_raw()
        duplicate_count = df["stock_code"].duplicated().sum()
        assert duplicate_count == 0, f"存在 {duplicate_count} 个重复代码"


class TestSupplementStockDetail:
    """测试 supplement_stock_detail() 函数"""

    def test_supplements_industry_column(self):
        """验证补充 industry 列"""
        # 准备测试数据（2只股票，减少 API 调用）
        test_df = pd.DataFrame({
            "stock_code": ["000001", "000002"],
            "stock_name": ["平安银行", "万科A"]
        })

        result = supplement_stock_detail(test_df)

        # 验证新列存在
        assert "industry" in result.columns
        assert "list_date" in result.columns
        assert "delist_date" in result.columns

    def test_preserves_original_data(self):
        """验证保留原始数据"""
        test_df = pd.DataFrame({
            "stock_code": ["000001"],
            "stock_name": ["平安银行"]
        })

        result = supplement_stock_detail(test_df)

        # 验证原始数据未丢失
        assert result["stock_code"].iloc[0] == "000001"
        assert result["stock_name"].iloc[0] == "平安银行"

    def test_has_industry_data(self):
        """验证行业数据被填充"""
        test_df = pd.DataFrame({
            "stock_code": ["000001", "000002"],
            "stock_name": ["平安银行", "万科A"]
        })

        result = supplement_stock_detail(test_df)

        # 至少有一只股票获取到行业信息
        valid_industries = result["industry"].notna().sum()
        assert valid_industries > 0, "未获取到任何行业信息"


class TestDatabaseSync:
    """测试数据库同步功能"""

    def test_sync_limited_stocks(self, db_session):
        """
        测试小范围股票同步（完整流程）
        使用事务回滚保护数据库
        """
        # 获取原始数据并限制为10只
        raw_df = get_stock_basic_raw()
        test_df = raw_df.head(10).copy()

        # 补充详情
        detailed_df = supplement_stock_detail(test_df)

        # 直接使用 Repository 层同步到数据库（使用测试的 session）
        success_count = 0

        for _, row in detailed_df.iterrows():
            try:
                # 使用 get_or_create 方法获取或创建股票
                stock = (
                    db_session.query(StockBasic)
                    .filter_by(stock_code=row["stock_code"])
                    .first()
                )

                if stock:
                    # 更新现有记录
                    stock.stock_name = row["stock_name"]
                    if "industry" in row and pd.notna(row["industry"]):
                        stock.industry = row["industry"]
                    if "list_date" in row and pd.notna(row["list_date"]):
                        stock.list_date = row["list_date"]
                    if "delist_date" in row and pd.notna(row["delist_date"]):
                        stock.delist_date = row["delist_date"]
                else:
                    # 创建新记录
                    stock = StockBasic(
                        stock_code=row["stock_code"],
                        stock_name=row["stock_name"],
                        industry=row.get("industry") if pd.notna(row.get("industry")) else None,
                        list_date=row.get("list_date") if pd.notna(row.get("list_date")) else None,
                        delist_date=row.get("delist_date") if pd.notna(row.get("delist_date")) else None,
                    )
                    db_session.add(stock)

                db_session.flush()  # 刷新但不提交
                success_count += 1
            except Exception as e:
                print(f"同步 {row['stock_code']} 失败: {e}")

        # 验证成功数量
        assert success_count >= 5, f"成功同步数量过低: {success_count}/10"

        # 验证数据库中的记录
        for code in test_df["stock_code"].head(5):
            record = db_session.query(StockBasic).filter_by(stock_code=code).first()
            assert record is not None, f"股票 {code} 未找到"
            assert record.stock_name is not None, f"股票 {code} 名称为空"

    def test_update_existing_stock(self, db_session):
        """测试更新已存在的股票"""
        # 先插入一条记录
        stock = StockBasic(
            stock_code="999999",
            stock_name="测试股票",
            list_date=None,
        )
        db_session.add(stock)
        db_session.flush()

        # 验证插入成功
        record = db_session.query(StockBasic).filter_by(stock_code="999999").first()
        assert record.stock_name == "测试股票"

        # 更新记录
        record.stock_name = "更新后的测试股票"
        db_session.flush()

        # 验证更新成功（需要刷新或重新查询）
        db_session.refresh(record)
        assert record.stock_name == "更新后的测试股票"
