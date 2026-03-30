"""测试航班数据API"""
import requests
import json
from datetime import datetime

# 测试几个可能的API

# 1. 飞常准API（需要key）
print("=== 测试API ===")

# 2. 尝试航班管家
url = "https://www.variflight.com/flight/fquery"
params = {
    'fnum': 'CZ',  # 南航
}

try:
    resp = requests.get(url, params=params, timeout=10)
    print(f"航班管家: {resp.status_code}")
    if resp.status_code == 200:
        print(f"响应长度: {len(resp.text)}")
except Exception as e:
    print(f"航班管家失败: {e}")

# 3. 尝试其他免费API
# 民航局API
url2 = "http://www.caac.gov.cn/api/flight"
try:
    resp = requests.get(url2, timeout=10)
    print(f"民航局: {resp.status_code}")
except Exception as e:
    print(f"民航局失败: {e}")

print("\n结论: 免费API大多需要注册或已下线")
print("建议: 使用付费API如 Aviationstack、Amadeus")
