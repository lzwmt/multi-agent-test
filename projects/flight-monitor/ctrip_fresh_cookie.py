"""获取携程新鲜Cookie"""
import json
import time
from playwright.sync_api import sync_playwright


def get_fresh_cookies():
    """获取新鲜Cookie"""
    print("=== 获取携程新鲜Cookie ===\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800},
        )

        page = context.new_page()

        # 访问携程
        url = "https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate=2026-03-14"
        print(f"访问: {url}")

        page.goto(url, wait_until='networkidle', timeout=60000)
        time.sleep(10)

        # 获取Cookie
        cookies = context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}

        print(f"\n获取到 {len(cookie_dict)} 个Cookie:")
        for name, value in cookie_dict.items():
            print(f"  {name}: {value[:50]}...")

        # 保存
        with open('/tmp/ctrip_fresh_cookies.json', 'w') as f:
            json.dump(cookie_dict, f, indent=2)
        print("\n✓ Cookie已保存到 /tmp/ctrip_fresh_cookies.json")

        browser.close()
        return cookie_dict


if __name__ == "__main__":
    get_fresh_cookies()
