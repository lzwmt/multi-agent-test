"""机票数据抓取模块 V2 - 多数据源"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re
import time
import random

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# 尝试导入 Scrapling
try:
    from scrapling.fetchers import StealthyFetcher
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

# 随机 User-Agent 列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
]


class FlightFetcher:
    """机票数据抓取器"""

    def _fetch_with_playwright(self, url: str, wait_time: int = 5000, stealth: bool = False) -> Optional[str]:
        """使用 Playwright 抓取页面，带超时控制和随机化
        
        Args:
            url: 目标URL
            wait_time: 等待时间（毫秒）
            stealth: 是否使用隐身模式（反检测）
        """
        # 随机延迟，避免请求过快
        time.sleep(random.uniform(1, 3))
        
        try:
            with sync_playwright() as p:
                if stealth:
                    # 隐身模式配置 - 使用隐私模式，禁用缓存
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                            '--disable-features=IsolateOrigins,site-per-process',
                            '--no-sandbox',
                            '--incognito',
                            '--disable-cache',
                            '--disable-application-cache',
                            '--disk-cache-size=0',
                        ]
                    )
                    context = browser.new_context(
                        viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                        user_agent=random.choice(USER_AGENTS),
                        locale='zh-CN',
                        timezone_id='Asia/Shanghai',
                    )
                    # 添加反检测脚本
                    context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                        window.chrome = { runtime: {} };
                    """)
                else:
                    # 普通模式 - 也使用随机 User-Agent
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent=random.choice(USER_AGENTS)
                    )
                
                page = context.new_page()
                
                try:
                    # 设置额外的请求头
                    page.set_extra_http_headers({
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    })
                    
                    page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    
                    # 模拟真实用户行为
                    if stealth:
                        # 随机滚动
                        for _ in range(random.randint(1, 3)):
                            page.evaluate(f'window.scrollBy(0, {random.randint(100, 500)})')
                            time.sleep(random.uniform(0.5, 1.5))
                        
                        # 随机鼠标移动
                        for _ in range(random.randint(2, 4)):
                            x = random.randint(100, 800)
                            y = random.randint(100, 600)
                            page.mouse.move(x, y)
                            time.sleep(random.uniform(0.3, 0.8))
                    
                    page.wait_for_timeout(wait_time)
                    html = page.content()
                    browser.close()
                    return html
                except PlaywrightTimeout:
                    browser.close()
                    return None
                except Exception as e:
                    browser.close()
                    return None
        except Exception as e:
            return None

    def fetch_ctrip(self, origin_code: str, dest_code: str, date: datetime) -> Optional[List[Dict]]:
        """从携程抓取航班价格"""
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://flights.ctrip.com/online/list/oneway-{origin_code}-{dest_code}?depdate={date_str}"

        print(f"  抓取携程：{origin_code}->{dest_code} {date.strftime('%m-%d')}", end=" ")

        try:
            # 携程用普通模式（隐身模式会超时）
            html = self._fetch_with_playwright(url, wait_time=6000, stealth=False)
            if not html:
                print("✗ 超时")
                return None
            
            flights = self._extract_ctrip_prices(html, date)
            print(f"✓ {len(flights)}条")
            return flights
        except Exception as e:
            print(f"✗ {e}")
            return None

    def _extract_ctrip_prices(self, html: str, date: datetime) -> List[Dict]:
        """从携程 HTML 中提取价格 - 精确版"""
        flights = []
        unique_prices = set()
        
        # 携程价格格式（处理HTML编码）：\u003cdfn\u003e¥\u003c/dfn\u003e575
        # 或正常格式：<dfn>¥</dfn>575
        price_patterns = [
            r'<dfn>¥</dfn>(\d+)',  # 正常格式
            r'\\u003cdfn\\u003e¥\\u003c/dfn\\u003e(\d+)',  # HTML编码格式
            r'"price"[^>]*>\s*<dfn>¥</dfn>(\d+)',  # 带price class
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                try:
                    price = int(match)
                    if 300 <= price <= 5000:  # 合理价格范围
                        unique_prices.add(price)
                except ValueError:
                    continue
        
        # 备用：从低价日历 tab 中提取
        tab_pattern = r'price:(\d+),date:(\d{4}-\d{2}-\d{2})'
        tab_matches = re.findall(tab_pattern, html)
        for price_str, date_str in tab_matches:
            try:
                price = int(price_str)
                if 300 <= price <= 5000 and date_str == date.strftime('%Y-%m-%d'):
                    unique_prices.add(price)
            except ValueError:
                continue
        
        # 过滤异常价格（整千的可能是默认值）
        filtered_prices = [p for p in unique_prices if p not in [1000, 2000, 5000, 10000]]
        
        for price in sorted(filtered_prices)[:5]:
            flights.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': price,
                'currency': 'CNY',
                'source': 'ctrip',
            })

        return flights

    def fetch_qunar(self, origin_code: str, dest_code: str, date: datetime) -> Optional[List[Dict]]:
        """从去哪儿网抓取航班价格 - 使用 Playwright 模拟点击"""
        print(f"  抓取去哪儿：{origin_code}->{dest_code} {date.strftime('%m-%d')}", end=" ")

        try:
            html = self._fetch_qunar_with_click(origin_code, dest_code, date)
            if not html:
                print("✗ 无数据")
                return None
            
            flights = self._extract_qunar_prices(html, date)
            print(f"✓ {len(flights)}条")
            return flights
        except Exception as e:
            print(f"✗ {e}")
            return None

    def _fetch_qunar_with_click(self, origin_code: str, dest_code: str, date: datetime) -> Optional[str]:
        """使用 Playwright 模拟点击搜索"""
        from playwright.sync_api import sync_playwright
        
        # 城市代码转名称映射（简化版）
        city_names = {
            'CAN': '广州',
            'TAO': '青岛',
            'PEK': '北京',
            'SHA': '上海',
            'SZX': '深圳',
            'CTU': '成都',
            'HGH': '杭州',
            'XIY': '西安',
        }
        
        origin_name = city_names.get(origin_code, origin_code)
        dest_name = city_names.get(dest_code, dest_code)
        date_str = date.strftime("%Y-%m-%d")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                # 打开首页
                page.goto("https://flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(2000)
                
                # 填写出发地
                from_input = page.locator('[placeholder="出发地"]').first
                if from_input.is_visible():
                    from_input.click()
                    page.wait_for_timeout(500)
                    from_input.fill(origin_name)
                    page.wait_for_timeout(1000)
                    page.locator(f'text={origin_name}').first.click()
                    page.wait_for_timeout(500)
                
                # 填写目的地
                to_input = page.locator('[placeholder="目的地"]').first
                if to_input.is_visible():
                    to_input.click()
                    page.wait_for_timeout(500)
                    to_input.fill(dest_name)
                    page.wait_for_timeout(1000)
                    page.locator(f'text={dest_name}').first.click()
                    page.wait_for_timeout(500)
                
                # 设置日期
                date_input = page.locator('[placeholder="出发日期"]').first
                if date_input.is_visible():
                    date_input.click()
                    page.wait_for_timeout(500)
                    # 清除并输入日期
                    date_input.fill(date_str)
                    page.wait_for_timeout(1000)
                    # 点击确认或空白处关闭日期选择器
                    page.locator('body').click()
                    page.wait_for_timeout(500)
                
                # 点击搜索
                search_btn = page.locator('text=搜索').first
                if search_btn.is_visible():
                    search_btn.click()
                    page.wait_for_timeout(10000)  # 等待结果加载
                
                html = page.content()
                browser.close()
                return html
            except Exception as e:
                browser.close()
                return None

    def _fetch_with_scrapling(self, url: str, wait_time: int = 8000) -> Optional[str]:
        """使用 Scrapling 抓取页面"""
        if not SCRAPLING_AVAILABLE:
            return None
        
        try:
            page = StealthyFetcher.fetch(
                url,
                headless=True,
                network_idle=True,
                wait=wait_time,
            )
            return page.css('body').get()
        except Exception as e:
            print(f"(Scrapling失败)")
            return None

    def _extract_qunar_prices(self, html: str, date: datetime) -> List[Dict]:
        """从去哪儿 HTML 中提取价格"""
        flights = []
        unique_prices = set()
        
        # 去哪儿价格格式
        patterns = [
            r'<div[^>]*class="[^"]*price[^"]*"[^>]*>\s*¥?\s*([\d,]+)',
            r'¥\s*([\d,]+)',
            r'([\d,]+)\s*元',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                try:
                    price = int(match.replace(',', ''))
                    if 200 <= price <= 8000:
                        unique_prices.add(price)
                except ValueError:
                    continue

        for price in sorted(unique_prices)[:5]:
            flights.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': price,
                'currency': 'CNY',
                'source': 'qunar',
            })

        return flights

    def fetch_tongcheng(self, origin_code: str, dest_code: str, date: datetime) -> Optional[List[Dict]]:
        """从同程旅行抓取航班价格 - 使用隐身模式"""
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://www.ly.com/flights/home?from={origin_code}&to={dest_code}&date={date_str}"

        print(f"  抓取同程：{origin_code}->{dest_code} {date.strftime('%m-%d')}", end=" ")

        try:
            # 使用隐身模式
            html = self._fetch_with_playwright(url, wait_time=10000, stealth=True)
            if not html:
                print("✗ 无数据")
                return None
            
            flights = self._extract_tongcheng_prices(html, date)
            print(f"✓ {len(flights)}条")
            return flights
        except Exception as e:
            print(f"✗ {e}")
            return None

    def _extract_tongcheng_prices(self, html: str, date: datetime) -> List[Dict]:
        """从同程 HTML 中提取价格"""
        flights = []
        unique_prices = set()
        
        # 同程价格格式
        patterns = [
            r'¥\s*([\d,]+)',
            r'([\d,]+)\s*元',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                try:
                    price = int(match.replace(',', ''))
                    if 200 <= price <= 8000:
                        unique_prices.add(price)
                except ValueError:
                    continue

        for price in sorted(unique_prices)[:5]:
            flights.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': price,
                'currency': 'CNY',
                'source': 'tongcheng',
            })

        return flights

    def fetch_all_sources(self, origin_code: str, dest_code: str, date: datetime) -> List[Dict]:
        """从所有数据源抓取某一天的航班价格"""
        all_flights = []
        
        sources = [
            ('ctrip', self.fetch_ctrip),
            ('qunar', self.fetch_qunar),
            ('tongcheng', self.fetch_tongcheng),
        ]
        
        for name, fetch_func in sources:
            flights = fetch_func(origin_code, dest_code, date)
            if flights:
                all_flights.extend(flights)
            time.sleep(1)
        
        return all_flights

    def fetch_multiple_days(self, origin_code: str, dest_code: str, days: int = 7) -> List[Dict]:
        """抓取多天的数据（从所有数据源）"""
        all_flights = []
        today = datetime.now()

        print(f"\n开始抓取 {origin_code}->{dest_code} 未来{days}天数据:\n")

        for i in range(days):
            date = today + timedelta(days=i)
            print(f"[{i+1}/{days}] {date.strftime('%Y-%m-%d')}:")
            
            flights = self.fetch_all_sources(origin_code, dest_code, date)
            if flights:
                all_flights.extend(flights)
            
            time.sleep(2)

        return all_flights


if __name__ == "__main__":
    fetcher = FlightFetcher()

    print("=" * 60)
    print("机票价格抓取测试 - 广州 (CAN) -> 青岛 (TAO)")
    print("=" * 60)
    
    results = fetcher.fetch_multiple_days("CAN", "TAO", days=3)
    
    print("\n" + "=" * 60)
    print(f"抓取完成，共 {len(results)} 条价格记录")
    print("=" * 60)
    
    if results:
        by_date = {}
        for r in results:
            date = r['date']
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(r)
        
        print("\n按日期统计:")
        for date in sorted(by_date.keys()):
            flights = by_date[date]
            sources = set(f['source'] for f in flights)
            prices = [f['price'] for f in flights]
            print(f"  {date}: {len(flights)}条记录 | 来源：{', '.join(sources)} | 价格范围：¥{min(prices)}-{max(prices)}")
        
        print("\n原始数据:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("\n未获取到任何数据")
