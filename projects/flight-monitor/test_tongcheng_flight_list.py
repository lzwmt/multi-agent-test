"""劫持同程航班列表API"""
import json
import time
from playwright.sync_api import sync_playwright


def hijack_tongcheng_flight_list(dep_code, arr_code, date_str):
    """劫持同程航班列表"""
    print(f"\n{'='*70}")
    print(f"[同程航班列表劫持] {dep_code} -> {arr_code}, {date_str}")
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
            
            # 劫持响应
            def handle_response(response):
                url = response.url
                if any(x in url.lower() for x in ['flight', 'list', 'search', 'api']) and response.status == 200:
                    try:
                        data = response.json()
                        data_str = json.dumps(data)
                        
                        # 检查是否包含航班列表数据
                        if any(x in data_str for x in ['flightNo', 'flightNumber', 'depTime', 'arrTime']):
                            print(f"\n[API] {url[:60]}...")
                            print(f"  数据大小: {len(data_str)} 字节")
                            api_calls.append({
                                'url': url,
                                'data': data,
                            })
                            
                            # 保存
                            with open(f'/tmp/tongcheng_flight_{len(api_calls)}.json', 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 访问同程航班列表页
            url = f"https://m.ly.com/flight/itinerary?dep={dep_code}&arr={arr_code}&date={date_str}"
            print(f"\n访问: {url}")
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(20)
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(api_calls)} 个航班列表API")
            print('='*70)
            
            for i, item in enumerate(api_calls[:5], 1):
                print(f"\n{i}. {item['url'][:80]}")
                # 简单分析
                data = item['data']
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            print(f"   {key}: {len(value)} 项")
            
            return api_calls
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    hijack_tongcheng_flight_list("CAN", "TAO", "2026-03-14")
