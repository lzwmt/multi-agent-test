"""测试 V3 通知格式"""
import json
from notifier import format_price_alert_message, format_daily_report

# 模拟数据（带时间信息）
test_flights = [
    {
        'date': '2026-03-12',
        'price': 200,
        'currency': 'CNY',
        'source': 'qunar',
        'flight_iata': 'CZ3799',
        'flight_number': '3799',
        'airline': 'CZ',
        'dep_time': '2026-03-12 11:00',
        'arr_time': '2026-03-12 13:55',
        'duration': 175,
    },
    {
        'date': '2026-03-12',
        'price': 332,
        'currency': 'CNY',
        'source': 'tongcheng',
        'flight_iata': '3U1389',
        'flight_number': '1389',
        'airline': '3U',
        'dep_time': '2026-03-12 11:00',
        'arr_time': '2026-03-12 13:55',
        'duration': 175,
    },
    {
        'date': '2026-03-12',
        'price': 400,
        'currency': 'CNY',
        'source': 'ctrip',
        'flight_iata': 'MF3642',
        'flight_number': '3642',
        'airline': 'MF',
        'dep_time': '2026-03-12 12:00',
        'arr_time': '2026-03-12 15:05',
        'duration': 185,
    },
]

print("=" * 70)
print("测试低价提醒")
print("=" * 70)

low_prices = [f for f in test_flights if f['price'] <= 350]
alert_msg = format_price_alert_message(low_prices)
print(alert_msg)

print("\n" + "=" * 70)
print("测试每日报告")
print("=" * 70)

report_msg = format_daily_report(test_flights)
print(report_msg)
