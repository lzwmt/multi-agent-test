"""捕获携程完整请求信息"""
import json
import time
from playwright.sync_api import sync_playwright


def capture_ctrip_request():
    """捕获携程完整请求"""
    print("=== 捕获携程完整请求 ===\n")

    request_info = None
    response_info = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1280, 'height': 800},
            )

            page = context.new_page()

            # 捕获请求
            def handle_route(route, request):
                nonlocal request_info
                if 'batchSearch' in request.url:
                    request_info = {
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(request.headers),
                        'post_data': request.post_data,
                    }
                    print(f"\n✓ 捕获到请求!")
                    print(f"  URL: {request.url[:60]}...")

                route.continue_()

            page.route("**/*", handle_route)

            # 捕获响应
            def handle_response(response):
                nonlocal response_info
                if 'batchSearch' in response.url and response.status == 200:
                    try:
                        data = response.json()
                        response_info = {
                            'url': response.url,
                            'status': response.status,
                            'data': data,
                        }
                        print(f"\n✓ 捕获到响应!")
                        print(f"  状态: {response.status}")
                        if data.get('data'):
                            print(f"  数据: {str(data['data'])[:100]}...")
                    except:
                        pass

            page.on('response', handle_response)

            # 访问页面
            url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"
            print(f"访问: {url}")

            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(20)

            browser.close()

            # 保存结果
            if request_info:
                with open('/tmp/ctrip_captured_request.json', 'w') as f:
                    json.dump(request_info, f, indent=2)
                print("\n✓ 请求已保存到 /tmp/ctrip_captured_request.json")

            if response_info:
                with open('/tmp/ctrip_captured_response.json', 'w') as f:
                    json.dump(response_info, f, indent=2)
                print("✓ 响应已保存到 /tmp/ctrip_captured_response.json")

            return request_info, response_info

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    capture_ctrip_request()
