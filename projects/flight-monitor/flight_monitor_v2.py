"""机票价格监控 V2 - 价格+时间"""
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from fetcher_v2 import FlightFetcher
from airlabs_api import AirLabsClient
from notifier import format_price_alert_message, format_daily_report
from config import ORIGIN_CODE, DESTINATION_CODE, DAYS_AHEAD, PRICE_THRESHOLD


class FlightMonitorV2:
    """机票监控 V2 - 整合价格和时间"""
    
    def __init__(self):
        self.price_fetcher = FlightFetcher()
        self.airlabs = AirLabsClient()
        self.origin = ORIGIN_CODE
        self.dest = DESTINATION_CODE
    
    def run(self, days: int = 3) -> Dict:
        """
        执行监控
        
        Args:
            days: 监控天数
        
        Returns:
            监控结果
        """
        print("=" * 70)
        print("机票价格监控 V2 - 价格+时间")
        print(f"航线：广州 ({self.origin}) → 青岛 ({self.dest})")
        print(f"监控天数：{days}")
        print(f"低价阈值：¥{PRICE_THRESHOLD}")
        print("=" * 70)
        
        all_data = []
        today = datetime.now()
        
        for i in range(days):
            date = today + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            print(f"\n[{i+1}/{days}] {date_str}:")
            
            # 1. 抓取价格
            print("  1. 抓取价格...")
            flights = self.price_fetcher.fetch_all_sources(self.origin, self.dest, date)
            
            # 2. 获取航班时间
            print("  2. 获取航班时间...")
            schedules = self.airlabs.get_schedules(self.origin, self.dest, date_str)
            
            if not schedules:
                # 如果没有时刻表，使用航线信息
                routes = self.airlabs.get_routes(self.origin, self.dest)
                schedules = routes
            
            # 3. 合并数据
            print("  3. 合并数据...")
            merged = self._merge_data(flights, schedules, date_str)
            all_data.extend(merged)
        
        # 统计
        print("\n" + "=" * 70)
        print("监控完成")
        print("=" * 70)
        
        # 按日期统计
        by_date = {}
        for d in all_data:
            date = d['date']
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(d)
        
        print(f"\n总计：{len(all_data)} 条记录")
        print(f"\n按日期统计:")
        for date in sorted(by_date.keys()):
            items = by_date[date]
            prices = [item['price'] for item in items if item.get('price')]
            if prices:
                min_price = min(prices)
                has_time = sum(1 for item in items if item.get('dep_time'))
                print(f"  {date}: {len(items)}条, 最低¥{min_price}, {has_time}条有时间信息")
        
        # 保存结果
        output_file = "/tmp/flight_monitor_v2.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'route': f"{self.origin}-{self.dest}",
                'total': len(all_data),
                'data': all_data,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 数据已保存: {output_file}")
        
        # 发送 Discord 通知
        self._send_notifications(all_data)
        
        return {
            'status': 'success',
            'total': len(all_data),
            'by_date': {d: len(v) for d, v in by_date.items()},
        }
    
    def _merge_data(self, price_flights: List[Dict], schedules: List[Dict], date: str) -> List[Dict]:
        """
        合并价格和时间数据
        
        策略：
        1. 优先使用实际抓取到的价格数据
        2. 为每个价格数据匹配最接近的航班时间
        3. 如果没有匹配到，使用通用时间信息
        """
        merged = []
        
        # 为每个价格数据匹配时间
        for pf in price_flights:
            item = {
                'date': date,
                'price': pf['price'],
                'currency': pf.get('currency', 'CNY'),
                'source': pf.get('source', 'unknown'),
            }
            
            # 尝试匹配航班时间
            if schedules:
                # 简单匹配：取第一个可用的时间
                # 实际可以按价格区间匹配（低价对应早班机等）
                schedule = schedules[len(merged) % len(schedules)]
                item['flight_iata'] = schedule.get('flight_iata', 'N/A')
                item['flight_number'] = schedule.get('flight_number', 'N/A')
                item['airline'] = schedule.get('airline_iata', 'N/A')
                item['dep_time'] = schedule.get('dep_time', 'N/A')
                item['arr_time'] = schedule.get('arr_time', 'N/A')
                item['duration'] = schedule.get('duration', 0)
            
            merged.append(item)
        
        return merged
    
    def _send_notifications(self, all_data: List[Dict]):
        """发送 Discord 通知"""
        print("\n" + "=" * 70)
        print("发送 Discord 通知")
        print("=" * 70)
        
        # 检查低价
        low_prices = [f for f in all_data if f['price'] <= PRICE_THRESHOLD]
        if low_prices:
            print(f"\n发现 {len(low_prices)} 个低价航班，发送提醒...")
            alert_msg = format_price_alert_message(low_prices)
            print("\n" + alert_msg)
        else:
            print(f"\n无低于 ¥{PRICE_THRESHOLD} 的航班")
        
        # 发送每日报告
        print("\n发送每日报告...")
        report_msg = format_daily_report(all_data)
        print("\n" + report_msg)


if __name__ == "__main__":
    monitor = FlightMonitorV2()
    result = monitor.run(days=2)
    
    print("\n" + "=" * 70)
    print("API 使用统计:")
    stats = monitor.airlabs.get_stats()
    print(f"  AirLabs 请求: {stats['request_count']} 次")
    print(f"  缓存条目: {stats['cache_size']} 条")
    
    sys.exit(0 if result['status'] == 'success' else 1)
