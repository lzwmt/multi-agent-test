"""测试多个日期的价格差异"""
from datetime import datetime, timedelta
from flight_monitor_v2 import FlightMonitorV2

class DateTestMonitor(FlightMonitorV2):
    def test_dates(self, dates: list):
        """测试多个日期"""
        print("=" * 70)
        print("多日期价格对比测试")
        print("=" * 70)
        
        results = {}
        
        for date_str in dates:
            print(f"\n{'='*70}")
            print(f"日期: {date_str}")
            print('='*70)
            
            from fetcher_v2 import FlightFetcher
            from airlabs_api import AirLabsClient
            
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 抓取价格
            print("\n抓取价格...")
            fetcher = FlightFetcher()
            flights = fetcher.fetch_all_sources(self.origin, self.dest, date)
            
            # 按数据源分组
            by_source = {}
            for f in flights:
                source = f['source']
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(f['price'])
            
            print(f"\n价格统计:")
            for source, prices in sorted(by_source.items()):
                print(f"  {source}: {len(prices)}条, ¥{min(prices)}-{max(prices)}, 平均¥{sum(prices)//len(prices)}")
            
            results[date_str] = by_source
        
        # 对比不同日期的价格
        print("\n" + "=" * 70)
        print("日期价格对比")
        print("=" * 70)
        
        # 获取所有数据源
        all_sources = set()
        for by_source in results.values():
            all_sources.update(by_source.keys())
        
        for source in sorted(all_sources):
            print(f"\n{source}:")
            for date_str in dates:
                if date_str in results and source in results[date_str]:
                    prices = results[date_str][source]
                    print(f"  {date_str}: ¥{min(prices)}-{max(prices)} (平均¥{sum(prices)//len(prices)})")
                else:
                    print(f"  {date_str}: 无数据")

if __name__ == "__main__":
    monitor = DateTestMonitor()
    
    # 测试多个日期
    dates = [
        '2026-03-12',  # 今天
        '2026-03-13',  # 明天
        '2026-03-14',  # 后天
        '2026-03-15',  # 大后天
        '2026-03-16',  # 第5天
    ]
    
    monitor.test_dates(dates)
