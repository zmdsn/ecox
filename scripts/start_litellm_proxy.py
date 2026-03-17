#!/usr/bin/env python3
"""启动 LiteLLM 代理服务器

提供统一的 LLM API 接口，支持多个模型提供商
"""
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="启动 LiteLLM 代理服务器")
    parser.add_argument(
        "--port",
        type=int,
        default=4000,
        help="监听端口 (默认: 4000)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="litellm_config.yaml",
        help="配置文件路径"
    )

    args = parser.parse_args()

    print(f"正在启动 LiteLLM 代理服务器...")
    print(f"配置文件: {args.config}")
    print(f"端口: {args.port}")
    print(f"API 地址: http://localhost:{args.port}")

    try:
        # 启动 LiteLLM
        cmd = [
            "litellm", "--config", args.config,
            "--port", str(args.port),
            "--detailed_debug"
        ]

        print(f"\n执行命令: {' '.join(cmd)}\n")

        subprocess.run(cmd, check=True)

    except KeyboardInterrupt:
        print("\nLiteLLM 代理服务器已停止")
    except FileNotFoundError:
        print("错误: 未找到 litellm 命令")
        print("请安装: pip install litellm[proxy]")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
