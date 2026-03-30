"""调试网络请求 - 查找API"""
from playwright.sync_api import sync_playwright
import json

url = "https://www.ly.com/flights/home?from=CAN&to=TAO&date=2026-03-14"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    
    # 监听网络请求
    api_responses = []
    
    def handle_response(response):
        try:
            if 'api' in response.url.lower() or 'flight' in response.url.lower():
                if response.status == 200:
                    try:
                        data = response.json()
                        api_responses.append({
                            'url': response.url,
                            'data': data
                        })
                    except:
                        pass
        except:
            pass
    
    page = context.new_page()
    page.on('response', handle_response)
    
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(10000)
    
    browser.close()

print(f"捕获到 {len(api_responses)} 个API响应")

for i, resp in enumerate(api_responses[:3]):
    print(f"\n=== API {i+1} ===")
    print(f"URL: {resp['url'][:100]}")
    
    # 尝试查找时间信息
    data_str = json.dumps(resp['data'])
    import re
    times = re.findall(r'(\d{2}:\d{2})', data_str)
    if times:
        print(f"找到时间: {times[:10]}")
