"""劫持去哪儿航班列表响应数据"""
from playwright.sync_api import sync_playwright
import json
import time


def hijack_flight_data(date_str: str):
    """劫持航班数据"""
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
                
                # 尝试多种可能的接口路径
                keywords = ['list', 'flight', 'search', 'query', 'oneway', 'airline', 'detail']
                if any(k in url.lower() for k in keywords) and response.status == 200:
                    try:
                        # 尝试解析 JSON
                        data = response.json()
                        print(f"\n[响应] {url[:60]}...")
                        
                        # 查找航班数据
                        data_str = json.dumps(data)
                        if any(x in data_str for x in ['flight', 'depTime', 'arrTime', 'flightNo']):
                            print(f"  ✓ 可能包含航班数据")
                            flight_data.append({
                                'url': url,
                                'data': data,
                            })
                            
                            # 保存
                            with open(f'/tmp/qunar_flight_{date_str}.json', 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 访问列表页
            list_url = f"https://m.flight.qunar.com/h5/flight/list?dep=%E5%B9%BF%E5%B7%9E&arr=%E9%9D%92%E5%B2%9B&flightType=1&startDate={date_str}"
            print(f"访问: {list_url}")
            
            page.goto(list_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(20)  # 等待所有请求完成
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持结果: {len(flight_data)} 个响应")
            print('='*70)
            
            for i, item in enumerate(flight_data, 1):
                print(f"\n{i}. {item['url'][:80]}")
                # 分析数据结构
                analyze_data(item['data'])
            
            return flight_data
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


def analyze_data(data):
    """分析数据结构"""
    if isinstance(data, dict):
        print(f"   键: {list(data.keys())[:10]}")
        
        # 查找航班数组
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                print(f"   {key}: 数组({len(value)}项)")
                if isinstance(value[0], dict):
                    print(f"     示例键: {list(value[0].keys())[:5]}")
            elif isinstance(value, dict):
                if 'flight' in str(value).lower() or 'time' in str(value).lower():
                    print(f"   {key}: 可能包含航班数据")


if __name__ == "__main__":
    print("=" * 70)
    print("去哪儿航班数据劫持")
    print("=" * 70)
    
    dates = ['2026-03-14']
    
    for date_str in dates:
        hijack_flight_data(date_str)
