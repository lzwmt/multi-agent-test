"""测试抓取3月14日的机票"""
from datetime import datetime
from flight_monitor_v2 import FlightMonitorV2

# 设置日期为3月14日
class MockMonitor(FlightMonitorV2):
    def run(self, target_date: str = None, days: int = 1):
        """执行监控 - 指定日期"""
        from datetime import datetime, timedelta
        from fetcher_v2 import FlightFetcher
        from airlabs_api import AirLabsClient
        from config import ORIGIN_CODE, DESTINATION_CODE, PRICE_THRESHOLD
        
        print("=" * 70)
        print("机票价格监控 - 指定日期测试")
        print(f"航线：广州 ({self.origin}) → 青岛 ({self.dest})")
        print("=" * 70)
        
        # 使用指定日期
        if target_date:
            date = datetime.strptime(target_date, '%Y-%m-%d')
        else:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        
        print(f"\n查询日期: {date_str}")
        
        # 1. 抓取价格
        print("\n1. 抓取价格...")
        fetcher = FlightFetcher()
        flights = fetcher.fetch_all_sources(self.origin, self.dest, date)
        
        print(f"\n抓取到 {len(flights)} 条价格记录:")
        for f in flights:
            print(f"  {f['source']}: ¥{f['price']}")
        
        # 2. 获取航班时间
        print("\n2. 获取航班时间...")
        airlabs = AirLabsClient()
        schedules = airlabs.get_schedules(self.origin, self.dest, date_str)
        
        print(f"\n获取到 {len(schedules)} 个航班时刻:")
        for s in schedules[:10]:
            print(f"  {s['flight_iata']}: {s['dep_time']} -> {s['arr_time']}")
        
        # 3. 合并数据
        print("\n3. 合并数据...")
        merged = []
        for i, pf in enumerate(flights):
            item = {
                'date': date_str,
                'price': pf['price'],
                'currency': pf.get('currency', 'CNY'),
                'source': pf.get('source', 'unknown'),
            }
            
            # 匹配航班时间
            if schedules:
                schedule = schedules[i % len(schedules)]
                item['flight_iata'] = schedule.get('flight_iata', 'N/A')
                item['dep_time'] = schedule.get('dep_time', 'N/A')
                item['arr_time'] = schedule.get('arr_time', 'N/A')
                item['duration'] = schedule.get('duration', 0)
            
            merged.append(item)
        
        print("\n" + "=" * 70)
        print("合并结果:")
        print("=" * 70)
        
        for m in merged:
            flight = m.get('flight_iata', '')
            dep = m.get('dep_time', '').split(' ')[-1] if m.get('dep_time') else ''
            arr = m.get('arr_time', '').split(' ')[-1] if m.get('arr_time') else ''
            print(f"  {flight}: ¥{m['price']} ({m['source']}) {dep}->{arr}")
        
        return merged

if __name__ == "__main__":
    monitor = MockMonitor()
    
    # 测试3月14日
    print("\n" + "=" * 70)
    print("测试 3月14日")
    print("=" * 70)
    result = monitor.run(target_date='2026-03-14')
    
    print("\n" + "=" * 70)
    print("测试 3月12日（今天）")
    print("=" * 70)
    result2 = monitor.run(target_date='2026-03-12')
