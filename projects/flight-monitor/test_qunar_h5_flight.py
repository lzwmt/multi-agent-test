"""使用 https://m.flight.qunar.com/h5/flight/ 获取航班详情"""
from playwright.sync_api import sync_playwright
import json
import time
import re


def get_flight_detail(date_str: str):
    """获取航班详情"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    flight_data = []
    
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
                
                if '/api/' in url and response.status == 200:
                    try:
                        data = response.json()
                        data_str = json.dumps(data)
                        
                        # 检查是否包含航班信息
                        if any(x in data_str.lower() for x in ['flightno', 'deptime', 'arrtime', 'flightnum']):
                            print(f"\n[航班数据] {url[:60]}...")
                            print(f"  数据大小: {len(data_str)} 字节")
                            flight_data.append({
                                'url': url,
                                'data': data,
                            })
                            
                            # 保存
                            filename = f'/tmp/qunar_flight_detail_{url.split("/")[-1].split("?")[0]}_{date_str}.json'
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"  ✓ 已保存到 {filename}")
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 1. 访问 H5 页面
            print("1. 访问 H5 页面...")
            page.goto("https://m.flight.qunar.com/h5/flight/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # 2. 填写出发地
            print("2. 填写出发地...")
            try:
                # 尝试多种选择器
                selectors = [
                    'input[placeholder*="出发"]',
                    '.from-city',
                    '[data-type="from"]',
                ]
                for sel in selectors:
                    elem = page.locator(sel).first
                    if elem.is_visible():
                        elem.click()
                        time.sleep(1)
                        elem.fill("广州")
                        time.sleep(1)
                        page.locator('text=广州').first.click()
                        time.sleep(1)
                        print("  ✓ 广州")
                        break
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 3. 填写目的地
            print("3. 填写目的地...")
            try:
                selectors = [
                    'input[placeholder*="到达"]',
                    '.to-city',
                    '[data-type="to"]',
                ]
                for sel in selectors:
                    elem = page.locator(sel).first
                    if elem.is_visible():
                        elem.click()
                        time.sleep(1)
                        elem.fill("青岛")
                        time.sleep(1)
                        page.locator('text=青岛').first.click()
                        time.sleep(1)
                        print("  ✓ 青岛")
                        break
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 4. 设置日期
            print("4. 设置日期...")
            try:
                date_input = page.locator('input[placeholder*="日期"]').first
                if date_input.is_visible():
                    date_input.click()
                    time.sleep(1)
                    day = int(date_str.split('-')[2])
                    page.locator(f'text={day}日').first.click()
                    time.sleep(1)
                    print(f"  ✓ {date_str}")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 5. 点击搜索
            print("5. 点击搜索...")
            try:
                search_btn = page.locator('text=搜索').first
                if search_btn.is_visible():
                    search_btn.click()
                    print("  ✓ 已点击搜索")
                    time.sleep(20)  # 等待数据加载
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 6. 提取页面数据
            print("6. 提取页面数据...")
            html = page.content()
            
            # 航班号
            flights = re.findall(r'([A-Z]{2}\d{3,4})', html)
            print(f"  航班号: {list(set(flights))[:10]}")
            
            # 时间
            times = re.findall(r'(\d{2}:\d{2})', html)
            print(f"  时间: {times[:10]}")
            
            # 价格
            prices = re.findall(r'¥\s*([\d,]+)', html)
            print(f"  价格: {list(set(prices))[:10]}")
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(flight_data)} 个航班数据响应")
            print('='*70)
            
            for i, item in enumerate(flight_data, 1):
                print(f"\n{i}. {item['url'][:80]}")
                data = item['data']
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            print(f"   {key}: {len(value)} 项")
                            if isinstance(value[0], dict):
                                print(f"     字段: {list(value[0].keys())[:8]}")
            
            return flight_data
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("使用 https://m.flight.qunar.com/h5/flight/ 获取航班详情")
    print("=" * 70)
    
    dates = ['2026-03-14', '2026-03-18']
    
    for date_str in dates:
        get_flight_detail(date_str)
