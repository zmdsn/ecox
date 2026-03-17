#!/usr/bin/env python3
"""启动 Ecox AI Agent 服务器

启动 FastAPI 服务器，提供 OpenAI 兼容的聊天 API
"""
import argparse
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="启动 Ecox AI Agent 服务器")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="绑定地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="监听端口 (默认: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载（开发模式）"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数（生产环境建议使用 CPU 核心数）"
    )

    args = parser.parse_args()

    print(f"正在启动 Ecox AI Agent 服务器...")
    print(f"地址: http://{args.host}:{args.port}")
    print(f"API 文档: http://{args.host}:{args.port}/docs")
    print(f"健康检查: http://{args.host}:{args.port}/health")

    try:
        import uvicorn
        from ecox.agent.server import app

        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1
        )

    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
