"""访问 jumpUrl 获取航班详情"""
from playwright.sync_api import sync_playwright
import json
import time
import urllib.parse


def get_flight_from_jumpurl(jump_url: str):
    """从 jumpUrl 获取航班详情"""
    print(f"\n{'='*70}")
    print(f"访问: {jump_url[:80]}...")
    print('='*70)
    
    flights = []
    
    try:
        with sync_playwright() as p:
            iphone_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15'
            
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=iphone_ua,
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 劫持响应
            def handle_response(response):
                url = response.url
                
                # 关注航班列表 API
                if any(x in url.lower() for x in ['list', 'flight', 'search']) and response.status == 200:
                    try:
                        data = response.json()
                        data_str = json.dumps(data)
                        
                        # 检查是否包含航班信息
                        if any(x in data_str for x in ['flightNo', 'depTime', 'arrTime']):
                            print(f"\n[航班数据] {url[:60]}...")
                            flights.append(data)
                            
                            # 保存
                            with open(f'/tmp/qunar_jump_flight.json', 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"  ✓ 已保存")
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 访问页面
            page.goto(jump_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(15)
            
            # 提取页面中的航班信息
            html = page.content()
            
            # 尝试多种模式
            import re
            
            # 航班号模式
            flight_pattern = r'([A-Z]{2}\d{3,4})'
            flights_no = re.findall(flight_pattern, html)
            
            # 时间模式
            time_pattern = r'(\d{2}:\d{2})'
            times = re.findall(time_pattern, html)
            
            print(f"\n页面提取:")
            print(f"  航班号: {list(set(flights_no))[:5]}")
            print(f"  时间: {times[:10]}")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    return flights


if __name__ == "__main__":
    print("=" * 70)
    print("访问 jumpUrl 获取航班详情")
    print("=" * 70)
    
    # 从之前的响应中获取 jumpUrl
    # 使用北京-兰州的示例
    jump_url = "https://touch.qunar.com/lowFlight/flightList?arr=%E5%85%B0%E5%B7%9E&monitorTime=1773317378148&endDate=&monitorLowestPrice=301&hybridid=flight_tejia&flightType=1&dep=%E5%8C%97%E4%BA%AC&tagNames=3%E6%9C%8816%E6%97%A5&targetPrice=210&bizSource=SUPER_LOW&cat=touch_flight_home_urban_information_flow_oneWayTrip&days=-1&targetTax=0&tag=-1&startDate=2026-03-16"
    
    get_flight_from_jumpurl(jump_url)
