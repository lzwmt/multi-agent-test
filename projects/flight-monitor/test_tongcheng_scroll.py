"""滚动页面触发同程航班数据加载"""
import json
import time
from playwright.sync_api import sync_playwright


def scrape_tongcheng_with_scroll(dep_code, arr_code, date_str):
    """滚动页面获取航班数据"""
    print(f"\n{'='*70}")
    print(f"[同程滚动抓取] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 访问页面
            url = f"https://m.ly.com/flight/itinerary?dep={dep_code}&arr={arr_code}&date={date_str}"
            print(f"\n访问: {url}")
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(5)
            
            # 滚动页面触发加载
            print("滚动页面...")
            for i in range(5):
                page.evaluate(f'window.scrollBy(0, 500)')
                time.sleep(2)
                print(f"  滚动 {i+1}/5")
            
            # 等待加载
            time.sleep(5)
            
            # 截图
            page.screenshot(path=f'/tmp/tongcheng_scroll_{date_str}.png')
            print("✓ 截图已保存")
            
            # 获取HTML
            html = page.content()
            
            # 查找航班信息
            import re
            print("\n查找航班信息...")
            
            # 航班号模式
            flights = re.findall(r'([A-Z]{2}\d{3,4})', html)
            unique_flights = list(set(flights))
            print(f"  航班号: {unique_flights[:10]}")
            
            # 时间模式
            times = re.findall(r'(\d{2}:\d{2})', html)
            print(f"  时间: {times[:10]}")
            
            # 价格模式
            prices = re.findall(r'¥\s*([\d,]+)', html)
            prices = [int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000]
            if prices:
                print(f"  价格: ¥{min(prices)} - ¥{max(prices)}")
            
            # 查找JSON数据
            json_matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if json_matches:
                print(f"\n  ✓ 找到 {len(json_matches)} 个JSON数据")
                try:
                    data = json.loads(json_matches[0])
                    with open(f'/tmp/tongcheng_state_{date_str}.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"  ✓ JSON已保存")
                except:
                    pass
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    scrape_tongcheng_with_scroll("CAN", "TAO", "2026-03-14")
