"""抓取去哪儿结果页 HTML 内容"""
from playwright.sync_api import sync_playwright
import json
import re
import time


def scrape_html(date_str: str):
    """抓取结果页 HTML"""
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
            page.goto("https://m.flight.qunar.com/h5/flight/", wait_until='domcontentloaded', timeout=30000)
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
                    time.sleep(20)  # 等待页面加载
            except Exception as e:
                print(f"  ✗ {e}")
            
            # 6. 等待航班列表加载
            print("6. 等待航班列表加载...")
            time.sleep(10)
            
            # 7. 抓取 HTML
            print("7. 抓取 HTML...")
            html = page.content()
            
            # 8. 提取数据
            print("8. 提取数据...")
            
            # 保存 HTML
            with open(f'/tmp/qunar_html_{date_str}.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"  ✓ HTML 已保存到 /tmp/qunar_html_{date_str}.html")
            
            # 提取航班号
            flight_nos = re.findall(r'([A-Z]{2}\d{3,4})', html)
            unique_flights = list(set(flight_nos))
            print(f"\n  航班号: {unique_flights[:10]}")
            
            # 提取时间
            times = re.findall(r'(\d{2}:\d{2})', html)
            print(f"  时间: {times[:10]}")
            
            # 提取价格
            prices = re.findall(r'¥\s*([\d,]+)', html)
            unique_prices = list(set(prices))
            print(f"  价格: {unique_prices[:10]}")
            
            # 尝试提取 JSON 数据
            print("\n9. 查找 JSON 数据...")
            json_matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if json_matches:
                print(f"  ✓ 找到 {len(json_matches)} 个 JSON 数据")
                try:
                    data = json.loads(json_matches[0])
                    with open(f'/tmp/qunar_json_{date_str}.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"  ✓ JSON 已保存")
                except Exception as e:
                    print(f"  ✗ JSON 解析失败: {e}")
            
            # 查找 script 标签中的数据
            print("\n10. 查找 script 数据...")
            script_pattern = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
            for i, script in enumerate(script_pattern[:5]):
                if 'flight' in script.lower() or 'price' in script.lower():
                    print(f"  Script {i}: 包含 flight/price 数据 ({len(script)} 字节)")
            
            browser.close()
            
            return {
                'flights': unique_flights,
                'times': times,
                'prices': unique_prices,
            }
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("抓取去哪儿结果页 HTML")
    print("=" * 70)
    
    dates = ['2026-03-14', '2026-03-18']
    
    for date_str in dates:
        scrape_html(date_str)
