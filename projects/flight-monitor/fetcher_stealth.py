"""机票数据抓取 - 高级隐身模式"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re
import time
import random

from playwright.sync_api import sync_playwright


class StealthFlightFetcher:
    """高级隐身机票抓取器"""

    def _create_stealth_browser(self):
        """创建隐身浏览器"""
        playwright = sync_playwright().start()
        
        # 使用更真实的浏览器配置
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        # 创建具有真实指纹的上下文
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            geolocation={'latitude': 23.1291, 'longitude': 113.2644},  # 广州
            permissions=['geolocation'],
            color_scheme='light',
        )
        
        # 添加反检测脚本
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            window.chrome = { runtime: {} };
        """)
        
        return playwright, browser, context

    def fetch_tongcheng_with_time(self, origin_code: str, dest_code: str, date: datetime) -> Optional[List[Dict]]:
        """从同程抓取航班价格和时间"""
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://www.ly.com/flights/home?from={origin_code}&to={dest_code}&date={date_str}"
        
        print(f"  抓取同程（隐身模式）: {origin_code}->{dest_code} {date.strftime('%m-%d')}", end=" ")
        
        try:
            playwright, browser, context = self._create_stealth_browser()
            page = context.new_page()
            
            # 设置更真实的请求头
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            })
            
            # 访问页面
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # 随机等待，模拟真实用户
            time.sleep(random.uniform(3, 5))
            
            # 模拟鼠标移动
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.5, 1.5))
            
            # 滚动页面
            for _ in range(random.randint(2, 4)):
                page.evaluate('window.scrollBy(0, window.innerHeight / 2)')
                time.sleep(random.uniform(1, 2))
            
            # 等待航班列表加载
            time.sleep(random.uniform(5, 8))
            
            # 获取页面内容
            html = page.content()
            text = page.inner_text('body')
            
            browser.close()
            playwright.stop()
            
            # 解析数据
            flights = self._parse_tongcheng_data(html, text, date)
            print(f"✓ {len(flights)}条")
            return flights
            
        except Exception as e:
            print(f"✗ {e}")
            return None

    def _parse_tongcheng_data(self, html: str, text: str, date: datetime) -> List[Dict]:
        """解析同程数据"""
        flights = []
        
        # 查找价格
        prices = re.findall(r'¥\s*([\d,]+)', html)
        unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
        
        # 查找时间
        times = re.findall(r'\b(\d{1,2}:\d{2})\b', text)
        unique_times = sorted(set(times))
        
        print(f"\n    找到 {len(unique_prices)} 个价格, {len(unique_times)} 个时间")
        
        # 组合数据（简化版，假设价格和时间按顺序对应）
        for i, price in enumerate(unique_prices[:5]):
            flight = {
                'date': date.strftime('%Y-%m-%d'),
                'price': price,
                'currency': 'CNY',
                'source': 'tongcheng',
            }
            # 尝试添加时间
            if i * 2 < len(unique_times):
                flight['dep_time'] = unique_times[i * 2]
            if i * 2 + 1 < len(unique_times):
                flight['arr_time'] = unique_times[i * 2 + 1]
            
            flights.append(flight)
        
        return flights


if __name__ == "__main__":
    fetcher = StealthFlightFetcher()
    
    print("=" * 60)
    print("隐身模式测试 - 同程")
    print("=" * 60)
    
    today = datetime.now()
    flights = fetcher.fetch_tongcheng_with_time('CAN', 'TAO', today)
    
    if flights:
        print(f"\n抓取到 {len(flights)} 条航班:")
        for f in flights:
            time_info = f"{f.get('dep_time', '?')}->{f.get('arr_time', '?')}" if 'dep_time' in f else "无时间"
            print(f"  {f['date']} {time_info} ¥{f['price']}")
    else:
        print("\n未抓取到数据")
