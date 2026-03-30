"""获取去哪儿航班列表（含时间）"""
from playwright.sync_api import sync_playwright
import json
import re
import time


def get_flight_list(date_str: str):
    """获取航班列表"""
    print(f"\n{'='*70}")
    print(f"日期: {date_str}")
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
            
            # 直接访问航班列表页
            list_url = f"https://m.flight.qunar.com/h5/flight/list?dep=%E5%B9%BF%E5%B7%9E&arr=%E9%9D%92%E5%B2%9B&flightType=1&startDate={date_str}"
            print(f"访问: {list_url}")
            
            page.goto(list_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(10)
            
            # 提取航班信息
            html = page.content()
            
            # 尝试多种模式匹配航班信息
            patterns = [
                # 航班号 + 时间
                r'(\d{2}:\d{2}).*?(\d{2}:\d{2}).*?([A-Z]{2}\d{3,4})',
                # 价格
                r'¥\s*([\d,]+)',
                # JSON 数据
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, html)
                if matches:
                    print(f"\n模式 {i+1} 匹配: {len(matches)} 个")
                    for m in matches[:5]:
                        print(f"  {m}")
            
            # 尝试提取 JSON 数据
            print("\n尝试提取 JSON 数据...")
            json_matches = re.findall(r'"flight[^"]*":\s*({[^}]+})', html)
            if json_matches:
                print(f"  找到 {len(json_matches)} 个 flight JSON")
                for j in json_matches[:3]:
                    try:
                        data = json.loads(j)
                        print(f"  {json.dumps(data, ensure_ascii=False)[:150]}")
                    except:
                        pass
            
            # 保存 HTML 查看
            with open(f'/tmp/qunar_list_{date_str}.html', 'w', encoding='utf-8') as f:
                f.write(html[:50000])
            print(f"\n✓ HTML 已保存到 /tmp/qunar_list_{date_str}.html")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    return flights


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿航班列表测试")
    print("=" * 70)
    
    dates = ['2026-03-14', '2026-03-18']
    
    for date_str in dates:
        get_flight_list(date_str)
