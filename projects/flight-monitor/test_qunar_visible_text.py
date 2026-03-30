"""提取去哪儿页面可见文本"""
from playwright.sync_api import sync_playwright
import json
import time


def extract_visible_text(date_str: str):
    """提取页面可见文本"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            iphone_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15'
            
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=iphone_ua,
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 1. 访问 H5 页面
            print("1. 访问 H5 页面...")
            page.goto("https://m.flight.qunar.com/h5/flight/", wait_until='networkidle', timeout=30000)
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
                    time.sleep(25)  # 等待页面完全加载
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 6. 提取可见文本
            print("6. 提取可见文本...")
            
            # 获取页面所有文本
            text = page.inner_text('body')
            
            # 保存文本
            with open(f'/tmp/qunar_text_{date_str}.txt', 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  ✓ 文本已保存到 /tmp/qunar_text_{date_str}.txt")
            
            # 显示前2000字符
            print(f"\n页面文本预览:")
            print(text[:2000])
            
            # 尝试提取航班信息
            print("\n7. 尝试提取航班信息...")
            
            # 查找包含航班信息的元素
            flight_elements = page.locator('[class*="flight"], [class*="list"], [class*="item"]').all()
            print(f"  找到 {len(flight_elements)} 个可能的航班元素")
            
            for i, elem in enumerate(flight_elements[:5]):
                try:
                    elem_text = elem.inner_text()
                    if any(x in elem_text for x in ['航班', '起飞', '降落', '价格', '¥']):
                        print(f"\n  元素 {i+1}:")
                        print(f"    {elem_text[:200]}")
                except:
                    pass
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 70)
    print("提取去哪儿页面可见文本")
    print("=" * 70)
    
    dates = ['2026-03-14']
    
    for date_str in dates:
        extract_visible_text(date_str)
