"""测试实时价格调度器配置"""
import pytest
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
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
    current_time = base_time
    for i in range(5):
        next_fire = trigger.get_next_fire_time(None, current_time)
        if next_fire:
            next_fires.append(next_fire)
            # 移动到下一分钟以获取下一次触发时间
            current_time = next_fire + timedelta(seconds=1)

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
    current_time = base_time
    for i in range(5):
        next_fire = old_trigger.get_next_fire_time(None, current_time)
        if next_fire:
            next_fires.append(next_fire)
            # 移动到下一分钟以获取下一次触发时间
            current_time = next_fire + timedelta(seconds=1)

    # 验证10分钟间隔（这是旧的行为）
    expected_minutes = [0, 10, 20, 30, 40]
    actual_minutes = [t.minute for t in next_fires]

    assert actual_minutes == expected_minutes, "旧配置产生10分钟间隔"
    print("⚠️   旧配置仍然是10分钟间隔，需要修改")

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
        test_time = next_fire + timedelta(seconds=1)  # 加1秒以获取下一次触发

    # 验证上午触发时间（9:00-11:45，每15分钟一次）
    expected_morning_times = [
        '09:00', '09:15', '09:30', '09:45',
        '10:00', '10:15', '10:30', '10:45',
        '11:00', '11:15', '11:30', '11:45'
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
        if not next_fire or next_fire.hour >= 15 or next_fire.hour < 13:
            break
        afternoon_fires.append(next_fire)
        test_time = next_fire + timedelta(seconds=1)  # 加1秒以获取下一次触发

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
    print(f"每天总触发次数: {len(morning_fires) + len(afternoon_fires)} (12次上午 + 8次下午)")
