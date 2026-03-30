"""使用代理的机票抓取器"""
import requests
from datetime import datetime
import json
import random
import time

# 免费代理列表（可能不稳定）
PROXIES = [
    None,  # 直连
    {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'},  # Clash
]

# 测试代理
def test_proxy(proxy):
    """测试代理是否可用"""
    try:
        resp = requests.get(
            'https://httpbin.org/ip',
            proxies=proxy,
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"代理可用: {proxy}, IP: {data.get('origin', 'unknown')}")
            return True
    except Exception as e:
        print(f"代理不可用: {proxy}, 错误: {e}")
    return False

# 获取可用代理
def get_working_proxy():
    """获取可用的代理"""
    for proxy in PROXIES:
        if test_proxy(proxy):
            return proxy
    return None

if __name__ == "__main__":
    print("测试代理...")
    working_proxy = get_working_proxy()
    if working_proxy:
        print(f"使用代理: {working_proxy}")
    else:
        print("使用直连")
