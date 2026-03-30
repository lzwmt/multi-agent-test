"""调试去哪儿页面 - 加长等待"""
from scrapling.fetchers import StealthyFetcher
import re

url = "https://flight.qunar.com/site/oneway_list.htm?searchDepartureAirport=CAN&searchArrivalAirport=TAO&searchDepartureTime=2026-03-14&startSearch=true"

print("正在抓取去哪儿（等待15秒）...")
page = StealthyFetcher.fetch(
    url,
    headless=True,
    network_idle=True,
    wait=15000,  # 加长等待
)

html = page.css('body').get()
print(f"页面长度: {len(html)}")

# 保存HTML
with open('/tmp/qunar_debug_v2.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 查找航班相关的内容
if '航班' in html or 'flight' in html.lower():
    print("✓ 页面包含航班数据")
else:
    print("✗ 页面没有航班数据（可能是JS未加载）")

# 查找价格
prices = re.findall(r'¥\s*(\d+)', html)
if prices:
    print(f"找到价格: {prices[:10]}")
else:
    print("未找到价格数据")
