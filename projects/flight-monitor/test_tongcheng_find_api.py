"""寻找同程真实航班数据API"""
import json
import time
from playwright.sync_api import sync_playwright


def find_tongcheng_real_api(dep_code, arr_code, date_str):
    """寻找真实航班API"""
    print(f"\n{'='*70}")
    print(f"[寻找同程真实API] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    api_calls = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 劫持所有响应
            def handle_response(response):
                url = response.url
                if '17u.cn' in url or 'ly.com' in url:
                    try:
                        data = response.json()
                        data_str = json.dumps(data)
                        
                        # 检查是否包含真实航班数据特征
                        if 'flight' in data_str.lower() or 'fn' in data_str:
                            # 检查是否有多个不同的时间
                            times = set()
                            for t in ['08:', '09:', '10:', '11:', '12:', '13:', '14:', '15:', '16:', '17:', '18:', '19:', '20:', '21:']:
                                if t in data_str:
                                    times.add(t)
                            
                            if len(times) >= 3:  # 有多个不同的时间
                                print(f"\n[可能的真实API] {url[:60]}...")
                                print(f"  不同时间段: {len(times)} 个")
                                api_calls.append({
                                    'url': url,
                                    'data': data,
                                })
                                
                                # 保存
                                with open(f'/tmp/tongcheng_real_{len(api_calls)}.json', 'w', encoding='utf-8') as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 访问页面
            url = f"https://m.ly.com/flight/itinerary?dep={dep_code}&arr={arr_code}&date={date_str}"
            print(f"\n访问: {url}")
            
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(15)
            
            # 点击筛选或排序，触发更多API
            print("\n尝试点击筛选...")
            try:
                # 尝试点击"仅看直飞"
                direct_filter = page.locator('text=仅看直飞').first
                if direct_filter.is_visible():
                    direct_filter.click()
                    print("  ✓ 点击'仅看直飞'")
                    time.sleep(5)
            except:
                pass
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"找到 {len(api_calls)} 个可能的API")
            print('='*70)
            
            for i, item in enumerate(api_calls, 1):
                print(f"\n{i}. {item['url'][:80]}")
                data = item['data']
                if isinstance(data, dict) and 'data' in data:
                    flight_data = data['data']
                    if isinstance(flight_data, dict):
                        for key in ['fl', 'flightList', 'flights', 'list']:
                            if key in flight_data:
                                flights = flight_data[key]
                                if isinstance(flights, list):
                                    print(f"   包含 {len(flights)} 个航班")
                                    # 检查时间多样性
                                    times = set()
                                    for f in flights[:5]:
                                        if isinstance(f, dict):
                                            dt = f.get('dt', '') or f.get('departureDateTime', '')
                                            if dt:
                                                times.add(dt[11:13] if len(dt) > 13 else dt[:2])
                                    print(f"   时间段: {sorted(times)}")
            
            return api_calls
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    find_tongcheng_real_api("CAN", "TAO", "2026-03-14")
