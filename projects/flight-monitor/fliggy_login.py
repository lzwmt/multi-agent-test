"""飞猪登录 - 保存登录状态"""
from playwright.sync_api import sync_playwright
import os
import time

# 用户数据目录，用于保存登录状态
USER_DATA_DIR = "/tmp/fliggy_user_data"


def login_fliggy():
    """登录飞猪并保存状态"""
    print("=" * 70)
    print("飞猪登录")
    print("=" * 70)
    print("\n请手动登录飞猪...")
    print("登录成功后，关闭浏览器窗口，登录状态将被保存。\n")
    
    with sync_playwright() as p:
        # 使用持久化上下文
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,  # 显示浏览器窗口
            args=['--disable-blink-features=AutomationControlled'],
        )
        
        page = context.new_page()
        
        # 打开飞猪
        page.goto("https://www.fliggy.com/")
        
        print("请在浏览器中完成登录...")
        print("登录成功后，关闭浏览器窗口。\n")
        
        # 等待浏览器关闭
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        context.close()
        print("\n✓ 登录状态已保存")


def test_with_saved_state(date_str: str):
    """使用保存的登录状态测试"""
    print(f"\n{'='*70}")
    print(f"使用保存的登录状态测试: {date_str}")
    print('='*70)
    
    if not os.path.exists(USER_DATA_DIR):
        print("✗ 未找到登录状态，请先运行登录脚本")
        return
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=True,
        )
        
        page = context.new_page()
        
        # 访问飞猪
        url = f"https://www.fliggy.com/?ttid=sem.000000736&needSearch=true&searchBy=1280&fromCity=CAN&toCity=TAO&depDate={date_str}"
        page.goto(url, wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(10000)
        
        html = page.content()
        print(f"页面长度: {len(html)}")
        
        title = page.title()
        print(f"页面标题: {title}")
        
        # 检查是否已登录
        if "登录" in title:
            print("✗ 未登录或登录已过期")
        else:
            print("✓ 已登录")
            # 查找价格
            import re
            prices = re.findall(r'¥\s*([\d,]+)', html)
            unique_prices = sorted(set(int(p.replace(',', '')) for p in prices if 200 <= int(p.replace(',', '')) <= 5000))
            print(f"找到价格: {unique_prices[:10]}")
        
        context.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        login_fliggy()
    else:
        # 测试
        test_with_saved_state("2026-03-14")
