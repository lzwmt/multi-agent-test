"""完整流程：首页 -> 搜索 -> 劫持航班数据"""
from playwright.sync_api import sync_playwright
import json
import time


def full_flow(date_str: str):
    """完整流程获取航班数据"""
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
                
                # 关注所有 API 响应
                if '/api/' in url and response.status == 200:
                    try:
                        data = response.json()
                        data_str = json.dumps(data)
                        
                        # 检查是否包含航班相关信息
                        if any(x in data_str.lower() for x in ['flight', 'deptime', 'arrtime', 'flightno', 'depart', 'arrive']):
                            print(f"\n[航班数据] {url[:60]}...")
                            flight_data.append({
                                'url': url,
                                'data': data,
                            })
                            
                            # 保存
                            filename = f'/tmp/qunar_flight_{url.split("/")[-1].split("?")[0]}_{date_str}.json'
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"  ✓ 已保存到 {filename}")
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 1. 访问首页
            print("1. 访问首页...")
            page.goto("https://m.flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # 2. 填写出发地
            print("2. 填写出发地...")
            try:
                from_input = page.locator('input[placeholder*="出发"]').first
                if from_input.is_visible():
                    from_input.click()
                    time.sleep(1)
                    from_input.fill("广州")
                    time.sleep(1)
                    page.locator('text=广州').first.click()
                    time.sleep(1)
                    print("  ✓ 广州")
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 3. 填写目的地
            print("3. 填写目的地...")
            try:
                to_input = page.locator('input[placeholder*="到达"]').first
                if to_input.is_visible():
                    to_input.click()
                    time.sleep(1)
                    to_input.fill("青岛")
                    time.sleep(1)
                    page.locator('text=青岛').first.click()
                    time.sleep(1)
                    print("  ✓ 青岛")
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
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(flight_data)} 个航班数据响应")
            print('='*70)
            
            for i, item in enumerate(flight_data, 1):
                print(f"\n{i}. {item['url'][:80]}")
                # 简单分析
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
    print("去哪儿完整流程劫持")
    print("=" * 70)
    
    dates = ['2026-03-14', '2026-03-18']
    
    for date_str in dates:
        full_flow(date_str)
