"""携程数据劫持器 V6 - 详细错误分析"""
import json
import time
import requests
from playwright.sync_api import sync_playwright


def test_ctrip_api():
    """测试携程API"""
    print("=== 携程API详细测试 ===\n")

    # 先用Playwright获取完整的请求信息
    print("第一步：用Playwright获取完整请求...")

    api_request = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800},
        )

        page = context.new_page()

        # 劫持请求
        def handle_route(route, request):
            nonlocal api_request
            if 'batchSearch' in request.url:
                api_request = {
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers,
                    'post_data': request.post_data,
                }
                print(f"\n✓ 劫持到API请求!")
                print(f"  URL: {request.url[:80]}")
                print(f"  Method: {request.method}")
                print(f"  Headers: {dict(list(request.headers.items())[:10])}")
            route.continue_()

        page.route("**/*", handle_route)

        # 访问页面
        url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"
        print(f"访问: {url}")

        page.goto(url, wait_until='networkidle', timeout=60000)
        time.sleep(15)

        browser.close()

    if not api_request:
        print("\n✗ 未劫持到API请求")
        return

    # 分析请求
    print("\n第二步：分析请求...")
    print(f"\n请求URL: {api_request['url']}")
    print(f"请求方法: {api_request['method']}")

    # 尝试复现请求
    print("\n第三步：复现请求...")

    headers = api_request['headers']
    post_data = api_request['post_data']

    # 解析post_data
    try:
        payload = json.loads(post_data)
        print(f"Payload: {json.dumps(payload, indent=2)[:500]}")
    except:
        print(f"Post data: {post_data[:200]}")
        payload = {}

    # 发送请求
    try:
        resp = requests.post(
            api_request['url'],
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"\n状态码: {resp.status_code}")
        print(f"响应: {resp.text[:500]}")

        if resp.status_code == 200:
            data = resp.json()
            if data.get('data'):
                print("\n✓ 成功!")
            else:
                print(f"\n✗ 失败: {data}")
    except Exception as e:
        print(f"\n✗ 错误: {e}")


if __name__ == "__main__":
    test_ctrip_api()
