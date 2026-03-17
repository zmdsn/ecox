"""数据查询工具"""
from typing import Dict, Any
from .base import Tool


class DataQueryTool(Tool):
    """数据查询工具"""

    @property
    def name(self) -> str:
        return "data_query"

    @property
    def description(self) -> str:
        return "执行SQL查询获取数据库中的数据"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL查询语句"
                }
            },
            "required": ["sql"]
        }

    async def execute(self, sql: str = None, **kwargs) -> Dict[str, Any]:
        """执行SQL查询

        Args:
            sql: SQL查询语句
            **kwargs: 其他参数（兼容基类接口）

        Returns:
            查询结果或错误信息
        """
        # 如果没有提供 SQL，返回提示
        if not sql:
            return {
                "error": "缺少SQL查询语句",
                "hint": "请提供具体的SQL查询语句"
            }

        from ...get_data import run_sql

        # 验证SQL是只读查询
        sql_stripped = sql.strip().upper()
        if not sql_stripped.startswith("SELECT"):
            return {
                "error": "只支持SELECT查询",
                "sql": sql
            }

        result = await self._run_query(sql)
        return result

    async def _run_query(self, sql: str) -> Dict[str, Any]:
        """异步执行查询"""
        import asyncio
        loop = asyncio.get_event_loop()
        from ...get_data import run_sql
        return await loop.run_in_executor(None, run_sql, sql)
