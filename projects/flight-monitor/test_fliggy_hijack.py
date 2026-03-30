"""劫持飞猪API请求"""
import json
import time
from playwright.sync_api import sync_playwright


def hijack_fliggy(dep_code, arr_code, date_str):
    """劫持飞猪API"""
    print(f"\n{'='*70}")
    print(f"[飞猪劫持] {dep_code} -> {arr_code}, {date_str}")
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
                if any(x in url.lower() for x in ['flight', 'search', 'price', 'api', 'mtop']) and response.status == 200:
                    try:
                        data = response.json()
                        data_str = json.dumps(data)
                        if 'price' in data_str.lower() or 'flight' in data_str.lower():
                            print(f"\n[API] {url[:60]}...")
                            print(f"  数据大小: {len(data_str)} 字节")
                            api_calls.append({
                                'url': url,
                                'data': data,
                            })
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 访问飞猪H5
            url = f"https://h5.m.taobao.com/trip/flight/search/index.html?depCity={dep_code}&arrCity={arr_code}&depDate={date_str}"
            print(f"访问: {url}")
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(20)
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(api_calls)} 个API")
            print('='*70)
            
            for i, item in enumerate(api_calls[:5], 1):
                print(f"\n{i}. {item['url'][:80]}")
                # 保存
                with open(f'/tmp/fliggy_api_{i}.json', 'w', encoding='utf-8') as f:
                    json.dump(item['data'], f, ensure_ascii=False, indent=2)
            
            return api_calls
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    hijack_fliggy("CAN", "TAO", "2026-03-14")
