"""调试去哪儿页面"""
from scrapling.fetchers import StealthyFetcher
import re

url = "https://flight.qunar.com/site/oneway_list.htm?searchDepartureAirport=CAN&searchArrivalAirport=TAO&searchDepartureTime=2026-03-14&startSearch=true"

print("正在抓取去哪儿...")
page = StealthyFetcher.fetch(
    url,
    headless=True,
    network_idle=True,
    wait=10000,
)

html = page.css('body').get()
print(f"页面长度: {len(html)}")

# 保存HTML
with open('/tmp/qunar_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("HTML已保存到 /tmp/qunar_debug.html")

# 查找价格相关的内容
print("\n查找价格模式:")

# 找 ¥ 符号附近的内容
yuan_matches = re.findall(r'.{0,50}¥.{0,50}', html)
for i, m in enumerate(yuan_matches[:10]):
    print(f"  {i+1}. {m}")

# 找 price 关键字
print("\n查找 price 关键字:")
price_matches = re.findall(r'.{0,50}[Pp]rice[^a-zA-Z].{0,50}', html)
for i, m in enumerate(price_matches[:5]):
    print(f"  {i+1}. {m}")

# 找3-4位数字（可能是价格）
print("\n查找可能的价格数字(200-2000):")
numbers = re.findall(r'\b([2-9]\d{2,3})\b', html)
unique_nums = sorted(set(int(n) for n in numbers if 200 <= int(n) <= 2000))[:15]
print(f"  {unique_nums}")
