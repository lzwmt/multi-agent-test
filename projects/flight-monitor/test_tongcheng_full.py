"""完整模拟同程搜索流程"""
import json
import time
from playwright.sync_api import sync_playwright


def scrape_tongcheng_full(dep_code, arr_code, date_str):
    """完整抓取同程"""
    print(f"\n{'='*70}")
    print(f"[同程完整流程] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    api_data = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 劫持响应
            def handle_response(response):
                url = response.url
                if 'preflights' in url and response.status == 200:
                    try:
                        data = response.json()
                        if data.get('success'):
                            print(f"\n[API] {url[:60]}...")
                            api_data.append(data)
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 1. 访问首页
            print("1. 访问同程首页...")
            page.goto("https://m.ly.com/flight/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # 2. 填写出发地
            print("2. 填写出发地...")
            try:
                # 查找出发地输入框
                from_input = page.locator('input[placeholder*="出发"]').first
                if from_input.is_visible():
                    from_input.click()
                    time.sleep(1)
                    from_input.fill("广州")
                    time.sleep(1)
                    # 选择城市
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
                    # 选择日期
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
                    time.sleep(15)
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 截图
            page.screenshot(path=f'/tmp/tongcheng_full_{date_str}.png')
            print("✓ 截图已保存")
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(api_data)} 个API响应")
            print('='*70)
            
            for i, data in enumerate(api_data, 1):
                flight_data = data.get('data', {})
                print(f"\n{i}. 出发地: {flight_data.get('a')}, 到达地: {flight_data.get('d')}")
                print(f"   最低价格: ¥{flight_data.get('lp', 0)}")
                
                # 保存
                with open(f'/tmp/tongcheng_full_{i}.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            return api_data
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    scrape_tongcheng_full("CAN", "TAO", "2026-03-14")
