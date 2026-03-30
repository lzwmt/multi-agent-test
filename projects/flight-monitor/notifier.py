"""Discord 通知模块"""
from typing import List, Dict
from datetime import datetime


def format_price_alert_message(alerts: List[Dict]) -> str:
    """
    格式化低价提醒消息 - V3 价格+时间版本

    Args:
        alerts: 低价提醒列表

    Returns:
        Discord 消息文本
    """
    if not alerts:
        return ""

    lines = [
        "🎉 **机票低价提醒**",
        f"航线: 广州 → 青岛",
        f"发现 {len(alerts)} 个低于阈值的航班",
        "",
    ]

    # 按价格排序
    sorted_alerts = sorted(alerts, key=lambda x: x.get('price', 0))

    for alert in sorted_alerts:
        price = alert.get('price', 0)
        date = alert.get('date', '未知')
        source = alert.get('source', '未知')
        flight = alert.get('flight_iata', '')
        dep_time = alert.get('dep_time', '')
        arr_time = alert.get('arr_time', '')
        duration = alert.get('duration', 0)
        
        # 格式化时间显示
        time_str = ""
        if dep_time and arr_time:
            # 提取时间部分
            dep = dep_time.split(' ')[-1] if ' ' in dep_time else dep_time
            arr = arr_time.split(' ')[-1] if ' ' in arr_time else arr_time
            time_str = f" {dep}→{arr}"
        
        flight_str = f" {flight}" if flight else ""
        duration_str = f" ({duration}分钟)" if duration else ""
        
        lines.append(
            f"📅 **{date}**{flight_str} - 💰 ¥{price}{time_str}{duration_str} ({source})"
        )

    lines.extend([
        "",
        f"⏰ 抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ])

    return "\n".join(lines)


def format_daily_report(flights: List[Dict]) -> str:
    """
    格式化每日价格报告 - V3 价格+时间版本

    Args:
        flights: 价格记录列表

    Returns:
        Discord 消息文本
    """
    if not flights:
        return "📊 暂无价格数据"

    # 按日期分组
    by_date = {}
    for f in flights:
        date = f.get('date', '未知')
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(f)

    lines = [
        "📊 **每日价格报告**",
        f"航线: 广州 → 青岛",
        f"数据条数: {len(flights)}",
        "",
    ]

    # 按日期显示
    for date in sorted(by_date.keys()):
        day_flights = by_date[date]
        prices = [f['price'] for f in day_flights]
        min_price = min(prices)
        max_price = max(prices)
        
        lines.append(f"**{date}** - {len(day_flights)}个航班")
        lines.append(f"💰 ¥{min_price} - ¥{max_price}")
        
        # 显示前3个最便宜的航班
        sorted_flights = sorted(day_flights, key=lambda x: x['price'])[:3]
        for f in sorted_flights:
            flight = f.get('flight_iata', '')
            dep = f.get('dep_time', '').split(' ')[-1] if f.get('dep_time') else ''
            arr = f.get('arr_time', '').split(' ')[-1] if f.get('arr_time') else ''
            price = f['price']
            source = f.get('source', '')
            
            flight_str = f" {flight}" if flight else ""
            time_str = f" {dep}→{arr}" if dep and arr else ""
            
            lines.append(f"  • ¥{price}{flight_str}{time_str} ({source})")
        
        lines.append("")

    lines.append(f"⏰ 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    test_alerts = [
        {'date': '2026-03-15', '价格': 90, 'price_cny': 486, 'currency': 'SGD', 'source': 'skyscanner'},
        {'date': '2026-03-18', '价格': 95, 'price_cny': 513, 'currency': 'SGD', 'source': 'skyscanner'},
    ]

    msg = format_price_alert_message(test_alerts)
    print("低价提醒消息:")
    print(msg)
    print("\n" + "="*50 + "\n")

    # 测试日报
    test_records = [
        {'date': '2026-03-11', '价格': 100, 'currency': 'SGD'},
        {'date': '2026-03-11', '价格': 120, 'currency': 'SGD'},
        {'date': '2026-03-11', '价格': 150, 'currency': 'SGD'},
    ]
    report = format_daily_report(test_records)
    print("每日报告:")
    print(report)
