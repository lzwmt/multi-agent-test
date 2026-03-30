"""去哪儿最佳实践 - 完整用户路径"""
from datetime import datetime
from playwright.sync_api import sync_playwright
import json
import re
import time
import random


def fetch_qunar_best(date_str: str):
    """最佳实践抓取"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--no-sandbox',
                ]
            )
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080},
            )
            
            page = context.new_page()
            
            # 1. 打开首页
            print("1. 打开首页...")
            page.goto("https://flight.qunar.com/", wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
            
            # 2. 点击出发地输入框
            print("2. 输入出发地...")
            from_input = page.locator('[placeholder="出发地"]').first
            from_input.click()
            time.sleep(0.5)
            
            # 模拟键盘输入（带延迟）
            for char in "广州":
                page.keyboard.type(char, delay=random.randint(100, 200))
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(1)
            page.keyboard.press('Enter')
            time.sleep(1)
            print("  ✓ 出发地：广州")
            
            # 3. 点击目的地输入框
            print("3. 输入目的地...")
            to_input = page.locator('[placeholder="目的地"]').first
            to_input.click()
            time.sleep(0.5)
            
            for char in "青岛":
                page.keyboard.type(char, delay=random.randint(100, 200))
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(1)
            page.keyboard.press('Enter')
            time.sleep(1)
            print("  ✓ 目的地：青岛")
            
            # 4. 设置日期（点击日期选择器）
            print("4. 设置日期...")
            date_input = page.locator('[placeholder="出发日期"]').first
            date_input.click()
            time.sleep(1)
            
            # 尝试点击具体日期
            # 解析日期 2026-03-12 -> 3月12日
            month_day = f"{int(date_str.split('-')[1])}月{int(date_str.split('-')[2])}日"
            print(f"  尝试点击: {month_day}")
            
            try:
                date_cell = page.locator(f'text={month_day}').first
                if date_cell.is_visible():
                    date_cell.click()
                    print(f"  ✓ 点击日期: {month_day}")
                else:
                    # 回退到输入
                    for char in date_str:
                        page.keyboard.type(char, delay=random.randint(50, 100))
                    time.sleep(0.5)
                    page.keyboard.press('Enter')
                    print(f"  ✓ 输入日期: {date_str}")
            except:
                # 直接输入
                for char in date_str:
                    page.keyboard.type(char, delay=random.randint(50, 100))
                time.sleep(0.5)
                page.keyboard.press('Enter')
                print(f"  ✓ 输入日期: {date_str}")
            
            time.sleep(1)
            
            # 5. 点击搜索按钮
            print("5. 点击搜索...")
            search_btn = page.locator('text=搜索').first
            
            # 模拟鼠标移动
            box = search_btn.bounding_box()
            if box:
                page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                time.sleep(0.5)
            
            search_btn.click()
            print("  ✓ 已点击搜索")
            
            # 6. 等待页面跳转和加载
            print("6. 等待页面加载...")
            time.sleep(15)
            
            # 7. 检查当前 URL
            current_url = page.url
            print(f"  当前 URL: {current_url}")
            
            # 8. 提取 window.QNR 数据
            print("7. 提取 window.QNR 数据...")
            
            qnr_data = page.evaluate('''() => {
                try {
                    return window.QNR || null;
                } catch(e) {
                    return null;
                }
            }''')
            
            if qnr_data:
                print(f"  ✓ 找到 window.QNR (类型: {type(qnr_data).__name__})")
                
                # 保存数据到文件查看
                with open(f'/tmp/qnr_{date_str}.json', 'w', encoding='utf-8') as f:
                    json.dump(qnr_data, f, ensure_ascii=False, indent=2)
                print(f"  ✓ 数据已保存到 /tmp/qnr_{date_str}.json")
                
                # 尝试查找价格
                qnr_str = json.dumps(qnr_data)
                prices = re.findall(r'["\']?price["\']?\s*[:=]\s*["\']?(\d+)', qnr_str)
                if prices:
                    unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 5000))
                    print(f"  ✓ 找到价格: {unique_prices[:15]}")
                    return unique_prices
                else:
                    print("  ⚠ 未在 QNR 中找到价格")
            else:
                print("  ✗ window.QNR 无数据")
            
            # 9. 回退：从 HTML 中提取价格
            print("8. 从 HTML 提取价格...")
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
    print("去哪儿最佳实践测试")
    print("=" * 70)
    
    dates = ['2026-03-12', '2026-03-14']
    
    results = {}
    for date_str in dates:
        prices = fetch_qunar_best(date_str)
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
