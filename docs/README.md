# Ecox 文档目录

本目录包含 Ecox 项目的所有文档。

## 目录结构

### `/`
根目录包含项目核心文档：
- **README.md** - 项目介绍和快速开始
- **CLAUDE.md** - Claude Code 工作指南（包含代码架构、常用命令）

### `docs/`
主文档目录，包含以下子目录：

#### `guides/`
使用指南和入门教程：
- **START_GUIDE.md** - Ecox AI Agent 服务启动指南

#### `development/`
开发相关文档：
- **IMPROVEMENTS.md** - 项目改进记录和优化历史

#### `plans/`
设计和实现计划（按时间倒序）：
- **2026-03-17-ecox-ai-agent-*.md** - AI Agent 设计和实现
- **2026-03-16-*.md** - 统一财务模型和数据质量重构
- **2026-03-03-*.md** - 财报下载和股票信息测试
- **2026-03-02-*.md** - 数据验证器设计和实现

#### 技术指南
- **data-quality-guide.md** - 数据质量验证指南
- **agent-usage.md** - Agent 使用文档

## 文档约定

### 命名规范
- 设计文档：`YYYY-MM-DD-<feature-name>-design.md`
- 实现计划：`YYYY-MM-DD-<feature-name>-implementation.md` 或 `implementation-plan.md`
- 指南文档：`<topic>-guide.md`
- 使用文档：`<component>-usage.md`

### 文档分类
- **guides/** - 面向用户的使用指南
- **development/** - 开发过程记录
- **plans/** - 技术设计和实现计划
- **根目录** - 技术参考文档

## 查找文档

根据需求快速定位：

- **我想开始使用** → 查看 `README.md` 和 `guides/START_GUIDE.md`
- **我想了解架构** → 查看 `CLAUDE.md` 中的代码架构部分
- **我想了解新功能** → 查看 `plans/` 中最新的设计文档
- **我想改进代码** → 查看 `development/IMPROVEMENTS.md` 和相关技术指南
- **我想验证数据** → 查看 `data-quality-guide.md`
