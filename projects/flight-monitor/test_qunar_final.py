"""去哪儿最终方案 - 基于成功版本 + QNR 提取"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import re
import time
import random

# 去哪儿 Cookie
qunar_cookies = [
    {"name": "_i", "value": "DFiEZCOjLGiAUHPL_CeRItNt5MAw", "url": "https://flight.qunar.com"},
    {"name": "_q", "value": "U.uslsuus1942", "url": "https://flight.qunar.com"},
    {"name": "_s", "value": "s_MU6GVX5WXLHZZVXCE22PLRDX7A", "url": "https://flight.qunar.com"},
    {"name": "_t", "value": "29664446", "url": "https://flight.qunar.com"},
    {"name": "_v", "value": "WmNyo_iK8V1KVfy4mzpu3YZvOW7LhqMML7i4SyKLnmWOfk6XWZg_8BtrEbhBqYvF7b-wnYMgjnh9cVEp8IIpkKqGGRPVxQfZ-2gP1uAKKJGdow9hldmpSTExu_t1_Zhv2pcv_k7nqs5xAYe_lMbcd0XcVadY2S2BYTEpyapaV6bF", "url": "https://flight.qunar.com"},
    {"name": "csrfToken", "value": "HySpnjeJLVxoFFpcnIlvOIHnJNbxHhGc", "url": "https://flight.qunar.com"},
    {"name": "fid", "value": "b1c59615-0d7a-496c-abf8-838a0a4321b4", "url": "https://flight.qunar.com"},
]


def fetch_qunar_final(date_str: str):
    """最终方案：模拟点击 + QNR 提取"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(qunar_cookies)
            
            page = context.new_page()
            
            # 1. 打开首页
            print("1. 打开首页...")
            page.goto("https://flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
            
            # 2. 填写出发地
            print("2. 填写出发地...")
            from_input = page.locator('[placeholder="出发地"]').first
            if from_input.is_visible():
                from_input.click()
                time.sleep(0.5)
                from_input.fill("广州")
                time.sleep(1)
                page.locator('text=广州').first.click()
                time.sleep(0.5)
                print("  ✓ 广州")
            
            # 3. 填写目的地
            print("3. 填写目的地...")
            to_input = page.locator('[placeholder="目的地"]').first
            if to_input.is_visible():
                to_input.click()
                time.sleep(0.5)
                to_input.fill("青岛")
                time.sleep(1)
                page.locator('text=青岛').first.click()
                time.sleep(0.5)
                print("  ✓ 青岛")
            
            # 4. 设置日期
            print("4. 设置日期...")
            date_input = page.locator('[placeholder="出发日期"]').first
            if date_input.is_visible():
                date_input.click()
                time.sleep(0.5)
                date_input.fill(date_str)
                time.sleep(1)
                page.locator('body').click()
                time.sleep(0.5)
                print(f"  ✓ {date_str}")
            
            # 5. 点击搜索
            print("5. 点击搜索...")
            search_btn = page.locator('text=搜索').first
            if search_btn.is_visible():
                search_btn.click()
                print("  ✓ 已点击搜索")
                time.sleep(15)
            
            # 6. 提取 window.QNR 数据
            print("6. 提取 window.QNR 数据...")
            
            qnr_data = page.evaluate('''() => {
                try {
                    return window.QNR || null;
                } catch(e) {
                    return null;
                }
            }''')
            
            if qnr_data:
                print(f"  ✓ 找到 window.QNR (类型: {type(qnr_data).__name__})")
                
                # 保存数据到文件
                with open(f'/tmp/qnr_{date_str}.json', 'w', encoding='utf-8') as f:
                    json.dump(qnr_data, f, ensure_ascii=False, indent=2)
                print(f"  ✓ 数据已保存到 /tmp/qnr_{date_str}.json")
                
                # 尝试查找价格
                qnr_str = json.dumps(qnr_data)
                prices = re.findall(r'["\']?price["\']?\s*[:=]\s*["\']?(\d+)', qnr_str)
                if prices:
                    unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 5000))
                    print(f"  ✓ 从 QNR 找到价格: {unique_prices[:15]}")
                    return unique_prices
            
            # 7. 回退：从 HTML 中提取价格
            print("7. 从 HTML 提取价格...")
            html = page.content()
            prices = re.findall(r'¥\s*([\d,]+)', html)
            unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
            
            if unique_prices:
                print(f"  ✓ 找到价格: {unique_prices[:15]}")
                return unique_prices
            else:
                print("  ✗ 未找到价格")
            
            browser.close()
            return []
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿最终方案测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    results = {}
    for date_str in dates:
        prices = fetch_qunar_final(date_str)
        results[date_str] = prices
    
    # 对比结果
    print("\n" + "=" * 70)
    print("结果对比")
    print("=" * 70)
    
    for date_str, prices in results.items():
        if prices:
            print(f"{date_str}: {prices[:10]}")
        else:
            print(f"{date_str}: 无数据")
