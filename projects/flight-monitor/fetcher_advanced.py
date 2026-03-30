"""高级隐身机票抓取器 - 更多反检测方法"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re
import time
import random

from playwright.sync_api import sync_playwright


# 更多随机 User-Agent
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# 反检测脚本 - 更完整版本
STEALTH_SCRIPT = """
// 覆盖 webdriver
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 覆盖 plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {name: "Chrome PDF Plugin", filename: "internal-pdf-viewer"},
        {name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai"},
        {name: "Native Client", filename: "internal-nacl-plugin"}
    ]
});

// 覆盖 languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en']
});

// 覆盖 platform
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32'
});

// 覆盖 hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8
});

// 覆盖 deviceMemory
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8
});

// 覆盖 maxTouchPoints
Object.defineProperty(navigator, 'maxTouchPoints', {
    get: () => 0
});

// Chrome 对象
window.chrome = {
    runtime: {},
    loadTimes: () => {},
    csi: () => {},
    app: {}
};

// Permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// WebGL
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) {
        return 'Intel Inc.';
    }
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter(parameter);
};

// Canvas
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

// 通知
window.Notification = window.Notification || {};
window.Notification.permission = 'default';
"""


class AdvancedFlightFetcher:
    """高级隐身机票抓取器"""
    
    def fetch_with_advanced_stealth(self, url: str, wait_time: int = 8000) -> Optional[str]:
        """使用高级隐身模式抓取"""
        # 随机延迟
        time.sleep(random.uniform(2, 5))
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--no-sandbox',
                        '--incognito',
                        '--disable-cache',
                        '--disable-application-cache',
                        '--disk-cache-size=0',
                        '--disable-gpu',
                        f'--window-size={random.randint(1200, 1920)},{random.randint(800, 1080)}',
                    ]
                )
                
                context = browser.new_context(
                    viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                    user_agent=random.choice(USER_AGENTS),
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                    color_scheme='light',
                    reduced_motion='no-preference',
                )
                
                # 添加高级反检测脚本
                context.add_init_script(STEALTH_SCRIPT)
                
                page = context.new_page()
                
                # 设置请求头
                page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                })
                
                # 访问页面
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # 模拟真实用户行为
                # 1. 随机滚动
                for _ in range(random.randint(2, 4)):
                    scroll_amount = random.randint(200, 600)
                    page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                    time.sleep(random.uniform(0.8, 2.0))
                
                # 2. 随机鼠标移动
                for _ in range(random.randint(3, 6)):
                    x = random.randint(100, 1000)
                    y = random.randint(100, 700)
                    page.mouse.move(x, y)
                    time.sleep(random.uniform(0.3, 0.8))
                
                # 3. 随机点击空白处
                if random.random() > 0.5:
                    page.mouse.click(random.randint(100, 500), random.randint(100, 500))
                    time.sleep(random.uniform(0.5, 1.0))
                
                # 等待加载
                page.wait_for_timeout(wait_time)
                
                html = page.content()
                browser.close()
                return html
                
        except Exception as e:
            print(f"抓取失败: {e}")
            return None


if __name__ == "__main__":
    fetcher = AdvancedFlightFetcher()
    
    # 测试不同日期
    dates = ['2026-03-12', '2026-03-14', '2026-03-16']
    
    for date_str in dates:
        url = f"https://flights.ctrip.com/online/list/oneway-CAN-TAO?depdate={date_str}"
        print(f"\n{'='*60}")
        print(f"测试日期: {date_str}")
        print(f"{'='*60}")
        
        html = fetcher.fetch_with_advanced_stealth(url)
        if html:
            print(f"页面长度: {len(html)}")
            
            # 查找价格
            prices = re.findall(r'<dfn>¥</dfn>(\d+)', html)
            unique_prices = sorted(set(int(p) for p in prices if 200 <= int(p) <= 2000))
            print(f"找到价格: {unique_prices[:10]}")
        else:
            print("抓取失败")
