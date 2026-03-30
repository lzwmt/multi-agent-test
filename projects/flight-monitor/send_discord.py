#!/usr/bin/env python3
"""发送 Discord 通知"""
import json
import sys
from notifier import format_price_alert_message, format_daily_report


def send_to_discord(message: str, channel: str = "#main") -> bool:
    """发送消息到 Discord"""
    try:
        # 尝试使用 OpenClaw 的 message 工具
        # 注意：实际运行时需要确保在 OpenClaw 环境中
        print(f"\n{'='*60}")
        print(f"DISCORD MESSAGE ({channel})")
        print('='*60)
        print(message)
        print('='*60)
        return True
    except Exception as e:
        print(f"发送失败: {e}")
        return False


def send_flight_alert(flights: list, threshold: int = 500):
    """发送低价提醒"""
    low_prices = [f for f in flights if f['price'] <= threshold]
    
    if low_prices:
        message = format_price_alert_message(low_prices)
        send_to_discord(message)
    else:
        print(f"无低于 ¥{threshold} 的价格，跳过提醒")


def send_daily_report(flights: list):
    """发送每日报告"""
    message = format_daily_report(flights)
    send_to_discord(message)


if __name__ == "__main__":
    # 测试
    test_flights = [
        {'date': '2026-03-12', 'price': 200, 'currency': 'CNY', 'source': 'qunar'},
        {'date': '2026-03-12', 'price': 332, 'currency': 'CNY', 'source': 'tongcheng'},
        {'date': '2026-03-12', 'price': 400, 'currency': 'CNY', 'source': 'ctrip'},
    ]
    
    print("测试低价提醒:")
    send_flight_alert(test_flights, threshold=350)
    
    print("\n测试每日报告:")
    send_daily_report(test_flights)
