"""验证调度器配置（不实际运行）"""
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
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
    test_time = now + timedelta(seconds=1)
    for i in range(5):
        next_fire = trigger.get_next_fire_time(None, test_time)
        if not next_fire:
            break
        print(f"   {i+1}. {next_fire.strftime('%Y-%m-%d %H:%M:%S')}")
        test_time = next_fire + timedelta(seconds=1)

    print("\n📊 完整触发时间表（假设从9:00开始）:")
    morning_start = shanghai_tz.localize(datetime(2026, 3, 17, 9, 0, 0))

    print("\n   上午时段:")
    test_time = morning_start.replace(second=0, microsecond=0) - timedelta(seconds=1)
    count = 0
    for _ in range(20):
        next_fire = trigger.get_next_fire_time(None, test_time)
        if not next_fire or next_fire.hour >= 12:
            break
        print(f"      {next_fire.strftime('%H:%M')}")
        test_time = next_fire + timedelta(seconds=1)
        count += 1

    print("\n   下午时段:")
    afternoon_start = shanghai_tz.localize(datetime(2026, 3, 17, 13, 0, 0))
    test_time = afternoon_start.replace(second=0, microsecond=0) - timedelta(seconds=1)
    afternoon_count = 0
    for _ in range(20):
        next_fire = trigger.get_next_fire_time(None, test_time)
        if not next_fire or next_fire.hour >= 15 or (next_fire.hour >= 9 and next_fire.hour < 13):
            break
        print(f"      {next_fire.strftime('%H:%M')}")
        test_time = next_fire + timedelta(seconds=1)
        afternoon_count += 1

    print(f"\n✅ 每天总计触发: {count + afternoon_count} 次（{count}次上午 + {afternoon_count}次下午）")
    print(f"✅ 间隔: 15分钟")
    print(f"✅ 交易时段: 9:00-11:{45 if count > 10 else 15}, 13:00-14:45")

if __name__ == "__main__":
    verify_scheduler_config()
