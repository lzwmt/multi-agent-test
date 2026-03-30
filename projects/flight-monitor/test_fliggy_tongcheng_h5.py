"""用Playwright抓取飞猪和同程H5页面"""
import json
import time
from playwright.sync_api import sync_playwright


def scrape_fliggy(dep_code, arr_code, date_str):
    """抓取飞猪H5"""
    print(f"\n{'='*70}")
    print(f"[飞猪H5] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 访问飞猪H5
            url = f"https://h5.m.taobao.com/trip/flight/search/index.html?depCity={dep_code}&arrCity={arr_code}&depDate={date_str}"
            print(f"访问: {url}")
            
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(10)
            
            # 截图
            page.screenshot(path=f'/tmp/fliggy_{date_str}.png')
            print("✓ 截图已保存")
            
            # 获取HTML
            html = page.content()
            
            # 查找价格
            import re
            prices = re.findall(r'¥\s*([\d,]+)', html)
            prices = [int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000]
            
            if prices:
                print(f"✓ 找到价格: ¥{min(prices)} - ¥{max(prices)}")
            else:
                print("⚠ 未找到价格")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")


def scrape_tongcheng(dep_code, arr_code, date_str):
    """抓取同程H5"""
    print(f"\n{'='*70}")
    print(f"[同程H5] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 访问同程H5
            url = f"https://m.ly.com/flight/itinerary?dep={dep_code}&arr={arr_code}&date={date_str}"
            print(f"访问: {url}")
            
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(10)
            
            # 截图
            page.screenshot(path=f'/tmp/tongcheng_{date_str}.png')
            print("✓ 截图已保存")
            
            # 获取HTML
            html = page.content()
            
            # 查找价格
            import re
            prices = re.findall(r'¥\s*([\d,]+)', html)
            prices = [int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000]
            
            if prices:
                print(f"✓ 找到价格: ¥{min(prices)} - ¥{max(prices)}")
            else:
                print("⚠ 未找到价格")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")


if __name__ == "__main__":
    scrape_fliggy("CAN", "TAO", "2026-03-14")
    scrape_tongcheng("CAN", "TAO", "2026-03-14")
