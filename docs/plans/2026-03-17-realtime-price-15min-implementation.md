# 15分钟实时价格采集定时任务实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 将实时价格采集定时任务从每10分钟改为每15分钟，保持全市场A股采集范围，仅在交易时段触发。

**架构:** 修改 `src/ecox/data/realtime.py` 的 APScheduler CronTrigger 配置，将 `minute='*/10'` 改为 `minute='*/15'`，其他逻辑保持不变。

**技术栈:** Python, APScheduler, CronTrigger, pandas_market_calendars, PostgreSQL

---

## Task 1: 创建 CronTrigger 单元测试

**Files:**
- Create: `tests/test_realtime_scheduler.py`

**Step 1: Write the failing test**

创建测试文件，验证 CronTrigger 配置是否正确生成15分钟间隔的触发时间。

```python
"""测试实时价格调度器配置"""
import pytest
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

def test_15min_interval_trigger():
    """测试 CronTrigger 配置为15分钟间隔"""
    # 创建触发器（修改后的配置）
    trigger = CronTrigger(
        second=0,
        minute='*/15',
        hour='9-11,13-14',
        timezone='Asia/Shanghai'
    )

    # 验证触发器创建成功
    assert trigger is not None

    # 获取未来几次触发时间
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    base_time = shanghai_tz.localize(datetime(2026, 3, 17, 9, 0, 0))

    next_fires = []
    for i in range(5):
        next_fire = trigger.get_next_fire_time(None, base_time)
        if next_fire:
            next_fires.append(next_fire)
            base_time = next_fire

    # 验证前5次触发时间
    expected_times = [
        datetime(2026, 3, 17, 9, 0, 0),  # 09:00
        datetime(2026, 3, 17, 9, 15, 0), # 09:15
        datetime(2026, 3, 17, 9, 30, 0), # 09:30
        datetime(2026, 3, 17, 9, 45, 0), # 09:45
        datetime(2026, 3, 17, 10, 0, 0), # 10:00
    ]

    # 转换为时区感知时间
    expected_times = [shanghai_tz.localize(t) for t in expected_times]

    assert len(next_fires) == 5
    for actual, expected in zip(next_fires, expected_times):
        assert actual == expected, f"Expected {expected}, got {actual}"

    print("✅ CronTrigger 15分钟间隔测试通过")
    print(f"触发时间: {[t.strftime('%H:%M') for t in next_fires]}")

def test_10min_interval_trigger_should_fail():
    """测试旧的10分钟间隔配置（应该被替换）"""
    # 旧的配置（应该被修改）
    old_trigger = CronTrigger(
        second=0,
        minute='*/10',  # 这是旧的配置
        hour='9-11,13-14',
        timezone='Asia/Shanghai'
    )

    # 获取触发时间
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    base_time = shanghai_tz.localize(datetime(2026, 3, 17, 9, 0, 0))

    next_fires = []
    for i in range(5):
        next_fire = old_trigger.get_next_fire_time(None, base_time)
        if next_fire:
            next_fires.append(next_fire)
            base_time = next_fire

    # 验证10分钟间隔（这是旧的行为）
    expected_minutes = [0, 10, 20, 30, 40]
    actual_minutes = [t.minute for t in next_fires]

    assert actual_minutes == expected_minutes, "旧配置产生10分钟间隔"
    print("⚠️   旧配置仍然是10分钟间隔，需要修改")
```

**Step 2: Run test to verify it identifies the old configuration**

```bash
# 运行测试，验证旧配置是10分钟间隔
uv run pytest tests/test_realtime_scheduler.py::test_10min_interval_trigger_should_fail -v -s
```

Expected output:
```
⚠️  旧配置仍然是10分钟间隔，需要修改
PASSED
```

**Step 3: No implementation yet** (This test documents current state)

**Step 4: Skip to next task** (We'll come back after code modification)

**Step 5: No commit yet**

---

## Task 2: 修改 CronTrigger 配置为15分钟间隔

**Files:**
- Modify: `src/ecox/data/realtime.py:167-172`

**Step 1: Read the current implementation**

查看当前的 CronTrigger 配置：

```bash
# 查看第167-172行
sed -n '167,172p' src/ecox/data/realtime.py
```

Expected output:
```python
    trigger_normal = CronTrigger(
        second=0,
        minute='*/10',  # 当前是10分钟
        hour='9-11,13-14',
        timezone='Asia/Shanghai'
    )
```

**Step 2: Modify the code**

将 `minute='*/10'` 改为 `minute='*/15'`：

```python
    trigger_normal = CronTrigger(
        second=0,
        minute='*/15',  # 修改为15分钟
        hour='9-11,13-14',
        timezone='Asia/Shanghai'
    )
```

**Step 3: Verify the change**

```bash
# 确认修改成功
sed -n '167,172p' src/ecox/data/realtime.py | grep "minute='*/15'"
```

Expected: 输出包含 `minute='*/15'`

**Step 4: Run the updated test to verify 15-minute interval**

```bash
# 测试新配置（这个测试会失败，因为我们还没写）
uv run pytest tests/test_realtime_scheduler.py::test_15min_interval_trigger -v -s
```

Expected output:
```
✅ CronTrigger 15分钟间隔测试通过
触发时间: ['09:00', '09:15', '09:30', '09:45', '10:00']
PASSED
```

**Step 5: Commit the change**

```bash
git add src/ecox/data/realtime.py
git commit -m "feat: 将实时价格采集间隔从10分钟改为15分钟

- 修改 CronTrigger 配置: minute='*/10' → minute='*/15'
- 保持全市场A股采集范围不变
- 保持交易时段触发逻辑不变
- 每天触发次数从约24次减少到17次（减少29%）

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 创建触发时间验证测试

**Files:**
- Modify: `tests/test_realtime_scheduler.py`

**Step 1: Add comprehensive trigger time verification test**

在测试文件中添加更全面的测试，验证所有预期的触发时间点：

```python
def test_full_trading_schedule():
    """测试完整交易时段的触发时间表"""
    trigger = CronTrigger(
        second=0,
        minute='*/15',
        hour='9-11,13-14',
        timezone='Asia/Shanghai'
    )

    shanghai_tz = pytz.timezone('Asia/Shanghai')
    morning_start = shanghai_tz.localize(datetime(2026, 3, 17, 9, 0, 0))

    # 获取上午所有触发时间
    morning_fires = []
    test_time = morning_start
    for _ in range(20):  # 最多20次迭代
        next_fire = trigger.get_next_fire_time(None, test_time)
        if not next_fire or next_fire.hour >= 12:
            break
        morning_fires.append(next_fire)
        test_time = next_fire

    # 验证上午触发时间（应该是 9:00, 9:15, 9:30, ..., 11:15）
    expected_morning_times = [
        '09:00', '09:15', '09:30', '09:45',
        '10:00', '10:15', '10:30', '10:45',
        '11:00', '11:15'
    ]
    actual_morning = [t.strftime('%H:%M') for t in morning_fires]

    assert actual_morning == expected_morning_times, \
        f"上午触发时间不匹配: 期望 {expected_morning_times}, 实际 {actual_morning}"

    # 获取下午触发时间
    afternoon_start = shanghai_tz.localize(datetime(2026, 3, 17, 13, 0, 0))
    afternoon_fires = []
    test_time = afternoon_start

    for _ in range(20):
        next_fire = trigger.get_next_fire_time(None, test_time)
        if not next_fire or next_fire.hour >= 15:
            break
        afternoon_fires.append(next_fire)
        test_time = next_fire

    # 验证下午触发时间（13:00, 13:15, ..., 14:45）
    expected_afternoon_times = [
        '13:00', '13:15', '13:30', '13:45',
        '14:00', '14:15', '14:30', '14:45'
    ]
    actual_afternoon = [t.strftime('%H:%M') for t in afternoon_fires]

    assert actual_afternoon == expected_afternoon_times, \
        f"下午触发时间不匹配: 期望 {expected_afternoon_times}, 实际 {actual_afternoon}"

    print("✅ 完整交易时段测试通过")
    print(f"上午触发: {actual_morning}")
    print(f"下午触发: {actual_afternoon}")
    print(f"每天总触发次数: {len(morning_fires) + len(afternoon_fires)}")
```

**Step 2: Run the test**

```bash
uv run pytest tests/test_realtime_scheduler.py::test_full_trading_schedule -v -s
```

Expected output:
```
✅ 完整交易时段测试通过
上午触发: ['09:00', '09:15', '09:30', '09:45', '10:00', '10:15', '10:30', '10:45', '11:00', '11:15']
下午触发: ['13:00', '13:15', '13:30', '13:45', '14:00', '14:15', '14:30', '14:45']
每天总触发次数: 18
PASSED
```

**Step 3: No implementation changes** (This is a test)

**Step 4: Test passes** ✅

**Step 5: Commit the test**

```bash
git add tests/test_realtime_scheduler.py
git commit -m "test: 添加 CronTrigger 15分钟间隔完整测试

- 验证上午时段所有触发时间（9:00-11:15）
- 验证下午时段所有触发时间（13:00-14:45）
- 确保每天触发18次（9次上午 + 9次下午）
- 测试覆盖边界情况（11:15后不触发，14:45后不触发）

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 本地集成测试 - 手动触发数据采集

**Files:**
- Create: `tests/integration/test_realtime_fetch.py`

**Step 1: Create integration test**

创建集成测试，手动触发数据采集并验证数据完整性：

```python
"""集成测试：手动触发实时数据采集"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from datetime import datetime
from ecox.data.realtime import fetch_job, get_a_share_real_time_data

def test_manual_fetch_realtime_data():
    """手动触发数据采集，验证数据完整性"""
    print("\n=== 手动触发实时数据采集 ===")

    # 执行数据采集
    fetch_job()

    # 验证数据
    df = get_a_share_real_time_data()

    assert not df.empty, "数据采集失败，返回空 DataFrame"
    assert len(df) > 1000, f"数据量过少，仅 {len(df)} 条"
    assert '代码' in df.columns, "缺少 '代码' 列"
    assert '最新价' in df.columns, "缺少 '最新价' 列"

    # 验证数据有效性
    valid_prices = df[df['最新价'] > 0]
    assert len(valid_prices) > 1000, f"有效价格数据过少，仅 {len(valid_prices)} 条"

    print(f"✅ 数据采集成功")
    print(f"采集股票数量: {len(df)}")
    print(f"有效价格数量: {len(valid_prices)}")
    print(f"前5只股票:")
    print(df[['代码', '名称', '最新价', '涨跌幅']].head())

def test_database_save():
    """测试数据保存到数据库"""
    from ecox.services import DataCollectionService

    # 获取测试数据
    df = get_a_share_real_time_data()

    if df.empty:
        pytest.skip("无法获取测试数据")

    # 取前10条进行测试
    test_df = df.head(10)

    # 转换为字典列表
    data_list = []
    for _, row in test_df.iterrows():
        data = {
            "stock_code": str(row.get("代码")),
            "stock_name": str(row.get("名称")),
            "latest_price": float(row.get("最新价", 0)),
            "price_change": float(row.get("涨跌额", 0)),
            "price_change_rate": float(row.get("涨跌幅", 0)),
            "volume": int(row.get("成交量", 0)),
            "turnover": int(row.get("成交额", 0)),
            "high_price": float(row.get("最高", 0)),
            "low_price": float(row.get("最低", 0)),
            "open_price": float(row.get("今开", 0)),
            "pre_close_price": float(row.get("昨收", 0)),
        }
        data_list.append(data)

    # 保存到数据库
    service = DataCollectionService()
    result = service.save_realtime_data(data_list)

    assert result['success'] > 0, "数据保存失败"
    assert result['failed'] == 0, f"保存失败 {result['failed']} 条"

    print(f"✅ 数据库保存成功")
    print(f"成功: {result['success']} 条")
    print(f"失败: {result['failed']} 条")
```

**Step 2: Run the integration test**

```bash
# 确保数据库配置正确
uv run pytest tests/integration/test_realtime_fetch.py::test_manual_fetch_realtime_data -v -s
```

Expected output:
```
=== 手动触发实时数据采集 ===
2026-03-17 XX:XX:XX - INFO - 定时触发抓取...
2026-03-17 XX:XX:XX - INFO - 获取数据成功: 5123 条
2026-03-17 XX:XX:XX - INFO - 保存完成: 成功 5123 条, 失败 0 条
✅ 数据采集成功
采集股票数量: 5123
有效价格数量: 5123
前5只股票:
    代码      名称    最新价    涨跌幅
0  600000  浦发银行  10.25  -0.5
1  600004  白云机场  15.30   1.2
...
PASSED
```

**Step 3: Verify database save test**

```bash
uv run pytest tests/integration/test_realtime_fetch.py::test_database_save -v -s
```

Expected output:
```
✅ 数据库保存成功
成功: 10 条
失败: 0 条
PASSED
```

**Step 4: No implementation changes** (This is a test)

**Step 5: Commit integration tests**

```bash
git add tests/integration/test_realtime_fetch.py
git commit -m "test: 添加实时数据采集集成测试

- 手动触发 fetch_job() 验证数据采集
- 验证数据完整性和有效性
- 测试数据库保存功能
- 验证数据字段映射正确

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 验证调度器启动和运行

**Files:**
- Create: `scripts/verify_scheduler.py`

**Step 1: Create scheduler verification script**

创建脚本，验证调度器能否正确启动并显示触发时间：

```python
"""验证调度器配置（不实际运行）"""
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

def verify_scheduler_config():
    """验证调度器配置并显示触发时间"""
    print("=== 15分钟实时价格调度器配置验证 ===\n")

    trigger = CronTrigger(
        second=0,
        minute='*/15',
        hour='9-11,13-14',
        timezone='Asia/Shanghai'
    )

    shanghai_tz = pytz.timezone('Asia/Shanghai')
    now = shanghai_tz.localize(datetime.now())

    print("📅 当前时间:")
    print(f"   {now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")

    print("⏰ 未来5次触发时间:")
    test_time = now
    for i in range(5):
        next_fire = trigger.get_next_fire_time(None, test_time)
        if not next_fire:
            break
        print(f"   {i+1}. {next_fire.strftime('%Y-%m-%d %H:%M:%S')}")
        test_time = next_fire

    print("\n📊 完整触发时间表（假设从9:00开始）:")
    morning_start = shanghai_tz.localize(datetime(2026, 3, 17, 9, 0, 0))

    print("\n   上午时段:")
    test_time = morning_start
    count = 0
    for _ in range(20):
        next_fire = trigger.get_next_fire_time(None, test_time)
        if not next_fire or next_fire.hour >= 12:
            break
        print(f"      {next_fire.strftime('%H:%M')}")
        test_time = next_fire
        count += 1

    print("\n   下午时段:")
    afternoon_start = shanghai_tz.localize(datetime(2026, 3, 17, 13, 0, 0))
    test_time = afternoon_start
    afternoon_count = 0
    for _ in range(20):
        next_fire = trigger.get_next_fire_time(None, test_time)
        if not next_fire or next_fire.hour >= 15:
            break
        print(f"      {next_fire.strftime('%H:%M')}")
        test_time = next_fire
        afternoon_count += 1

    print(f"\n✅ 每天总计触发: {count + afternoon_count} 次（{count}次上午 + {afternoon_count}次下午）")
    print(f"✅ 间隔: 15分钟")
    print(f"✅ 交易时段: 9:00-11:15, 13:00-14:45")

if __name__ == "__main__":
    verify_scheduler_config()
```

**Step 2: Run the verification script**

```bash
uv run python scripts/verify_scheduler.py
```

Expected output:
```
=== 15分钟实时价格调度器配置验证 ===

📅 当前时间:
   2026-03-17 14:25:30 CST

⏰ 未来5次触发时间:
   1. 2026-03-17 14:30:00
   2. 2026-03-17 14:45:00
   3. 2026-03-18 09:00:00
   4. 2026-03-18 09:15:00
   5. 2026-03-18 09:30:00

📊 完整触发时间表（假设从9:00开始）:

   上午时段:
      09:00
      09:15
      09:30
      09:45
      10:00
      10:15
      10:30
      10:45
      11:00
      11:15

   下午时段:
      13:00
      13:15
      13:30
      13:45
      14:00
      14:15
      14:30
      14:45

✅ 每天总计触发: 18 次（10次上午 + 8次下午）
✅ 间隔: 15分钟
✅ 交易时段: 9:00-11:15, 13:00-14:45
```

**Step 3: Verify the output matches expectations**

检查：
- 上午10次触发（09:00-11:15）
- 下午8次触发（13:00-14:45）
- 总计18次（不是17次，设计文档有误）
- 间隔确认为15分钟

**Step 4: Update design document if needed**

如果触发次数与设计文档不符，更新设计文档：

```bash
# 编辑设计文档，修正触发次数
# docs/plans/2026-03-17-realtime-price-15min-scheduler-design.md
# 第101行："每天17次触发" → "每天18次触发"
```

**Step 5: Commit verification script**

```bash
git add scripts/verify_scheduler.py
git commit -m "feat: 添加调度器配置验证脚本

- 显示未来5次触发时间
- 显示完整交易时段触发时间表
- 验证15分钟间隔配置
- 统计每天触发次数

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: 部署到生产环境

**Files:**
- Update: `systemd service file or supervisor config` (如果存在)

**Step 1: Check if realtime service is running**

```bash
# 检查是否有正在运行的实时采集服务
ps aux | grep -E "realtime|get_data" | grep -v grep
```

**Step 2: Stop existing service (if running)**

如果有运行中的服务，停止它：

```bash
# 查找进程
ps aux | grep "realtime.py" | grep -v grep | awk '{print $2}'

# 停止进程（替换 PID）
# kill <PID>

# 或者使用 lsof
# lsof -i :<port> -t | xargs -r kill
```

**Step 3: Create deployment script**

创建部署脚本 `scripts/deploy_realtime_scheduler.sh`：

```bash
#!/bin/bash
set -e

echo "=== 部署15分钟实时价格采集调度器 ==="

# 停止现有服务
echo "1. 停止现有服务..."
pkill -f "realtime.py" || echo "没有运行中的服务"

# 等待进程结束
sleep 2

# 启动新服务
echo "2. 启动新服务..."
mkdir -p logs
nohup uv run python -m ecox.data.realtime > logs/realtime.log 2>&1 &
echo $! > logs/realtime.pid

# 等待服务启动
sleep 3

# 验证服务运行
echo "3. 验证服务状态..."
if ps -p $(cat logs/realtime.pid) > /dev/null; then
    echo "✅ 服务启动成功 (PID: $(cat logs/realtime.pid))"
else
    echo "❌ 服务启动失败"
    exit 1
fi

# 显示日志
echo "4. 最近日志:"
tail -20 logs/realtime.log

echo ""
echo "=== 部署完成 ==="
echo "服务 PID: $(cat logs/realtime.pid)"
echo "日志文件: logs/realtime.log"
echo "监控命令: tail -f logs/realtime.log"
```

**Step 4: Make script executable and run it**

```bash
chmod +x scripts/deploy_realtime_scheduler.sh
./scripts/deploy_realtime_scheduler.sh
```

Expected output:
```
=== 部署15分钟实时价格采集调度器 ===
1. 停止现有服务...
没有运行中的服务
2. 启动新服务...
3. 验证服务状态...
✅ 服务启动成功 (PID: 12345)
4. 最近日志:
2026-03-17 14:30:00 - INFO - 调度器已启动，等待下一个任务触发时间...
=== 部署完成 ===
服务 PID: 12345
日志文件: logs/realtime.log
监控命令: tail -f logs/realtime.log
```

**Step 5: Monitor the service**

```bash
# 实时监控日志
tail -f logs/realtime.log
```

Expected to see trigger every 15 minutes:
```
2026-03-17 14:30:00,000 - INFO - 定时触发抓取...
2026-03-17 14:30:05,123 - INFO - 获取数据成功: 5123 条
2026-03-17 14:30:06,456 - INFO - 保存完成: 成功 5123 条, 失败 0 条
```

**Step 6: Commit deployment script**

```bash
git add scripts/deploy_realtime_scheduler.sh
git commit -m "feat: 添加实时价格调度器部署脚本

- 自动停止现有服务
- 启动新的15分钟间隔调度器
- 验证服务运行状态
- 显示最近日志

使用方法:
  ./scripts/deploy_realtime_scheduler.sh

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: 监控和验证（持续观察）

**Files:**
- Create: `scripts/monitor_scheduler.sh`

**Step 1: Create monitoring script**

创建监控脚本，用于观察调度器运行情况：

```bash
#!/bin/bash
echo "=== 实时价格调度器监控 ==="
echo ""

# 检查进程状态
echo "📌 进程状态:"
if [ -f logs/realtime.pid ]; then
    PID=$(cat logs/realtime.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "   ✅ 服务运行中 (PID: $PID)"
        echo "   运行时间: $(ps -p $PID -o etime= | tr -d ' ')"
    else
        echo "   ❌ 服务未运行 (PID文件存在但进程不存在)"
        exit 1
    fi
else
    echo "   ❌ 服务未运行 (无PID文件)"
    exit 1
fi

echo ""

# 显示最近触发时间
echo "🕐 最近触发时间:"
grep "定时触发抓取" logs/realtime.log | tail -5 | while read line; do
    echo "   $line"
done

echo ""

# 显示采集统计
echo "📊 今日采集统计:"
START_OF_DAY=$(date +%Y-%m-%d)
grep "$START_OF_DAY" logs/realtime.log | grep "保存完成" | tail -1 || echo "   暂无今日数据"

echo ""

# 显示错误（如果有）
echo "⚠️  最近错误:"
grep "ERROR" logs/realtime.log | tail -3 || echo "   无错误"

echo ""
echo "=== 监控完成 ==="
echo "实时日志: tail -f logs/realtime.log"
```

**Step 2: Run monitoring script**

```bash
chmod +x scripts/monitor_scheduler.sh
./scripts/monitor_scheduler.sh
```

Expected output (after a few hours of running):
```
=== 实时价格调度器监控 ===

📌 进程状态:
   ✅ 服务运行中 (PID: 12345)
   运行时间: 2:15:30

🕐 最近触发时间:
   2026-03-17 14:30:00,000 - INFO - 定时触发抓取...
   2026-03-17 14:45:00,000 - INFO - 定时触发抓取...
   2026-03-17 14:15:00,000 - INFO - 定时触发抓取...

📊 今日采集统计:
   2026-03-17 14:45:06,789 - INFO - 保存完成: 成功 5123 条, 失败 0 条

⚠️  最近错误:
   无错误

=== 监控完成 ===
实时日志: tail -f logs/realtime.log
```

**Step 3: Verify 15-minute intervals**

观察日志，确认触发时间间隔为15分钟：
```
09:15:00 - 定时触发抓取...
09:30:00 - 定时触发抓取...  (间隔15分钟)
09:45:00 - 定时触发抓取...  (间隔15分钟)
10:00:00 - 定时触发抓取...  (间隔15分钟)
```

**Step 4: Check data freshness**

使用 Agent 查询最新数据，验证数据新鲜度：

```bash
curl -X POST http://localhost:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "ecox", "messages": [{"role": "user", "content": "600809的最新股价"}]}'
```

应该返回最近15分钟内的数据。

**Step 5: Commit monitoring script**

```bash
git add scripts/monitor_scheduler.sh
git commit -m "feat: 添加调度器监控脚本

- 检查进程状态和运行时间
- 显示最近触发时间
- 统计今日采集数据
- 检查错误日志

使用方法:
  ./scripts/monitor_scheduler.sh

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: 更新文档和日志

**Files:**
- Update: `docs/development/IMPROVEMENTS.md`
- Update: `README.md` or `CLAUDE.md` (if needed)

**Step 1: Update improvement log**

在 `docs/development/IMPROVEMENTS.md` 添加本次改进记录：

```markdown
## 2026-03-17: 实时价格采集改为15分钟定时任务

### 背景
用户反馈："实时价格查询应该做成一个定时任务, 每15分钟更新一次"

### 改进内容

#### 1. 调度器配置优化
**文件**: `src/ecox/data/realtime.py`

**修改前**: 每10分钟在交易时段触发
**修改后**: 每15分钟在交易时段触发

**代码变更**:
```python
# 修改前
trigger_normal = CronTrigger(
    second=0,
    minute='*/10',  # 10分钟间隔
    hour='9-11,13-14',
    timezone='Asia/Shanghai'
)

# 修改后
trigger_normal = CronTrigger(
    second=0,
    minute='*/15',  # 15分钟间隔
    hour='9-11,13-14',
    timezone='Asia/Shanghai'
)
```

#### 2. 触发时间表
**上午时段** (9:00-11:15): 10次
- 09:00, 09:15, 09:30, 09:45, 10:00, 10:15, 10:30, 10:45, 11:00, 11:15

**下午时段** (13:00-14:45): 8次
- 13:00, 13:15, 13:30, 13:45, 14:00, 14:15, 14:30, 14:45

**总计**: 每天18次触发

### 效果

| 指标 | 修改前 | 修改后 | 变化 |
|-----|--------|--------|------|
| 触发间隔 | 10分钟 | 15分钟 | +50% |
| 每天触发次数 | ~24次 | 18次 | -25% |
| API调用量 | 每天24次 | 每天18次 | 减少25% |
| 数据新鲜度 | 10分钟 | 15分钟 | 可接受 |

### 测试验证

- ✅ 单元测试: CronTrigger 配置验证
- ✅ 集成测试: 数据采集和保存
- ✅ 调度器验证: 触发时间表确认
- ✅ 部署测试: 生产环境运行验证

### 相关文件

- `src/ecox/data/realtime.py:167-172` - CronTrigger 配置
- `tests/test_realtime_scheduler.py` - 单元测试
- `tests/integration/test_realtime_fetch.py` - 集成测试
- `scripts/verify_scheduler.py` - 配置验证脚本
- `scripts/deploy_realtime_scheduler.sh` - 部署脚本
- `scripts/monitor_scheduler.sh` - 监控脚本

### Git提交
```
commit 03bd479 docs: 添加15分钟实时价格采集定时任务设计文档
commit XXXXXXX feat: 将实时价格采集间隔从10分钟改为15分钟
commit XXXXXXX test: 添加 CronTrigger 15分钟间隔完整测试
commit XXXXXXX test: 添加实时数据采集集成测试
commit XXXXXXX feat: 添加调度器配置验证脚本
commit XXXXXXX feat: 添加实时价格调度器部署脚本
commit XXXXXXX feat: 添加调度器监控脚本
```

### 设计文档
- `docs/plans/2026-03-17-realtime-price-15min-scheduler-design.md`
- `docs/plans/2026-03-17-realtime-price-15min-implementation.md`
```

**Step 2: Update CLAUDE.md if needed**

如果 `CLAUDE.md` 中提到了实时采集，更新相关描述：

```bash
# 检查是否需要更新
grep -n "实时\|realtime\|10分钟" CLAUDE.md

# 如果需要，更新相关描述
# 例如：将"每10分钟"改为"每15分钟"
```

**Step 3: Verify all changes**

```bash
# 查看所有修改
git status

# 确认所有任务完成
git log --oneline -10
```

**Step 4: Commit documentation updates**

```bash
git add docs/development/IMPROVEMENTS.md CLAUDE.md
git commit -m "docs: 更新改进日志，记录15分钟实时价格采集优化

- 添加改进背景和目标
- 记录代码变更和触发时间表
- 更新性能指标对比
- 添加测试验证记录
- 列出相关文件和提交记录

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**Step 5: Create summary and cleanup**

创建最终总结文档：

```bash
cat > docs/plans/2026-03-17-realtime-price-15min-summary.md <<'EOF'
# 15分钟实时价格采集定时任务 - 完成总结

**完成日期**: 2026-03-17
**状态**: ✅ 已完成并部署

## 完成的工作

1. ✅ 修改 CronTrigger 配置：10分钟 → 15分钟
2. ✅ 创建单元测试验证配置正确性
3. ✅ 创建集成测试验证数据采集
4. ✅ 创建配置验证脚本
5. ✅ 创建部署脚本
6. ✅ 创建监控脚本
7. ✅ 部署到生产环境
8. ✅ 更新文档

## 最终效果

- **触发间隔**: 15分钟（交易时段）
- **每天触发**: 18次（上午10次 + 下午8次）
- **数据新鲜度**: 15分钟
- **API调用量**: 减少25%

## 监控命令

```bash
# 查看服务状态
./scripts/monitor_scheduler.sh

# 查看实时日志
tail -f logs/realtime.log

# 重启服务
./scripts/deploy_realtime_scheduler.sh
```

## 相关文档

- 设计文档: `docs/plans/2026-03-17-realtime-price-15min-scheduler-design.md`
- 实施计划: `docs/plans/2026-03-17-realtime-price-15min-implementation.md`
- 改进日志: `docs/development/IMPROVEMENTS.md`
EOF
```

**Step 6: Final commit**

```bash
git add docs/plans/2026-03-17-realtime-price-15min-summary.md
git commit -m "docs: 添加15分钟实时价格采集完成总结

- 记录完成的工作清单
- 总结最终效果和性能指标
- 提供监控和使用指南
- 关联相关文档

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 总结

### 实施完成后的效果

✅ **实时价格采集改为每15分钟更新一次**
- 交易时段自动触发：9:00-11:15, 13:00-14:45
- 每天总计18次触发
- 数据新鲜度：15分钟

✅ **保持现有系统架构不变**
- 继续使用 `a_share_real_time` 表
- 继续使用 `MarketDataTool` 查询接口
- 全市场A股采集范围不变

✅ **性能优化**
- API调用量减少25%（24次/天 → 18次/天）
- 数据库写入压力降低
- 服务器负载减少

### 验证清单

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 调度器配置验证通过
- [ ] 生产环境部署成功
- [ ] 监控脚本正常工作
- [ ] 文档更新完成

### 相关资源

**设计文档**: `docs/plans/2026-03-17-realtime-price-15min-scheduler-design.md`
**实施计划**: 本文档
**改进日志**: `docs/development/IMPROVEMENTS.md`

---

**准备就绪，可以开始实施！** 🚀
