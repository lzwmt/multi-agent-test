"""机票数据抓取模块"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re

from scrapling.fetchers import StealthyFetcher


class FlightFetcher:
    """机票数据抓取器"""

    def __init__(self):
        self.fetcher = StealthyFetcher()

    def fetch_skyscanner(self, origin_code: str, dest_code: str, date: datetime) -> Optional[List[Dict]]:
        """
        从 Skyscanner 抓取航班价格

        Args:
            origin_code: 出发机场代码 (如 CAN)
            dest_code: 到达机场代码 (如 TAO)
            date: 出发日期

        Returns:
            航班列表，每个航班包含价格、时间、航空公司等信息
        """
        # 构建 URL
        date_str = date.strftime("%y%m%d")
        url = f"https://www.skyscanner.com/transport/flights/{origin_code.lower()}/{dest_code.lower()}/{date_str}/?adults=1&cabinclass=economy"

        print(f"抓取 Skyscanner: {url}")

        try:
            # 使用 stealthy-fetch 绕过反爬
            page = self.fetcher.fetch(
                url,
                headless=True,
                network_idle=True,
                wait=3000,  # 等待 3 秒让价格加载
            )

            # 提取价格数据
            flights = self._parse_skyscanner_page(page, date)
            return flights

        except Exception as e:
            print(f"抓取失败: {e}")
            return None

    def _parse_skyscanner_page(self, page, date: datetime) -> List[Dict]:
        """解析 Skyscanner 页面，提取航班信息"""
        flights = []

        # 获取页面文本内容
        html_content = page.css('body').get()

        # 尝试提取价格数据
        # Skyscanner 的价格通常在特定元素中
        price_elements = page.css('[data-testid="price"]')

        for elem in price_elements:
            price_text = elem.css('::text').get()
            if price_text:
                # 解析价格数字
                price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                if price_match:
                    price = int(price_match.group().replace(',', ''))
                    flights.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'price': price,
                        'price_text': price_text,
                        'source': 'skyscanner',
                    })

        return flights

    def fetch_flight_data(self, origin_code: str, dest_code: str, days_ahead: int = 30) -> List[Dict]:
        """
        抓取未来 N 天的航班数据

        Args:
            origin_code: 出发机场代码
            dest_code: 到达机场代码
            days_ahead: 监控未来天数

        Returns:
            所有日期的航班数据
        """
        all_flights = []
        today = datetime.now()

        for i in range(days_ahead):
            date = today + timedelta(days=i)
            print(f"\n抓取日期: {date.strftime('%Y-%m-%d')}")

            flights = self.fetch_skyscanner(origin_code, dest_code, date)
            if flights:
                all_flights.extend(flights)
                print(f"获取到 {len(flights)} 条价格数据")
            else:
                print("未获取到数据")

        return all_flights


if __name__ == "__main__":
    # 测试
    fetcher = FlightFetcher()

    # 测试抓取明天
    from datetime import datetime
    tomorrow = datetime.now() + timedelta(days=1)

    result = fetcher.fetch_skyscanner("CAN", "TAO", tomorrow)
    print(f"\n结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
