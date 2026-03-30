"""飞书多维表格存储模块"""
from typing import List, Dict
from datetime import datetime


def get_or_create_bitable():
    """获取或创建飞书多维表格"""
    # 这里使用 feishu_bitable_app 工具
    # 实际调用会在主程序中通过工具完成
    pass


def format_flight_records(flights: List[Dict]) -> List[Dict]:
    """
    将航班数据格式化为飞书表格记录格式

    Args:
        flights: 原始航班数据列表

    Returns:
        格式化后的记录列表
    """
    records = []

    for flight in flights:
        # 日期转换为毫秒时间戳
        from datetime import datetime
        date_obj = datetime.strptime(flight['date'], '%Y-%m-%d')
        date_timestamp = int(date_obj.timestamp() * 1000)
        
        record = {
            "日期": date_timestamp,
            "价格": flight['price'],
            "货币": flight.get('currency', 'CNY'),
            "数据源": flight.get('source', 'skyscanner'),
            "抓取时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "航线": "广州-青岛",
        }
        records.append(record)

    return records


def check_price_alert(records: List[Dict], threshold: int = 500) -> List[Dict]:
    """
    检查是否有低于阈值的价格

    Args:
        records: 价格记录列表
        threshold: 价格阈值（人民币）

    Returns:
        低于阈值的记录列表
    """
    alerts = []
    for record in records:
        price = record.get('价格', 0)
        
        if price <= threshold:
            alert = {
                **record,
                'price_cny': price,
                'threshold': threshold,
            }
            alerts.append(alert)

    return alerts


if __name__ == "__main__":
    # 测试
    test_flights = [
        {'date': '2026-03-11', 'price': 90, 'currency': 'SGD', 'source': 'skyscanner'},
        {'date': '2026-03-12', 'price': 120, 'currency': 'SGD', 'source': 'skyscanner'},
    ]

    records = format_flight_records(test_flights)
    print("格式化记录:")
    for r in records:
        print(r)

    alerts = check_price_alert(test_flights, threshold=500)
    print("\n低价提醒:")
    for a in alerts:
        print(f"日期: {a['date']}, 价格: {a['price_cny']} CNY")
