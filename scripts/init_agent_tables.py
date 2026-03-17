#!/usr/bin/env python3
"""初始化 Agent 数据库表

创建 agent_messages 和 agent_conversations 表
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ecox.agent.models.message import Base
from ecox.database import DatabaseSession


def init_tables():
    """初始化所有 Agent 表"""
    print("正在初始化 Ecox Agent 数据库表...")

    try:
        # 获取数据库引擎
        db = DatabaseSession()
        engine = db.get_engine()

        # 创建所有表
        Base.metadata.create_all(engine)

        print("✓ Agent 数据库表初始化成功！")
        print("\n已创建以下表:")
        print("  - agent_messages: 消息表")
        print("  - agent_conversations: 对话表")

        return True

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return False


if __name__ == "__main__":
    success = init_tables()
    sys.exit(0 if success else 1)
