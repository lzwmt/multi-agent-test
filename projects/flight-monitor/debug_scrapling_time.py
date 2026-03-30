"""用 Scrapling 抓取时间信息"""
from scrapling.fetchers import StealthyFetcher
import re

# 测试同程
url = "https://www.ly.com/Flight/QueryFlight.aspx?from=CAN&to=TAO&date=2026-03-14"

print("=== 用 Scrapling 抓取同程 ===")
page = StealthyFetcher.fetch(
    url,
    headless=True,
    network_idle=True,
    wait=10000,
)

html = page.css('body').get()
text = page.text

print(f"页面长度: {len(html)}")

# 查找时间
times = re.findall(r'\b(\d{1,2}:\d{2})\b', text)
unique_times = sorted(set(times))
print(f"找到 {len(unique_times)} 个时间: {unique_times[:20]}")

# 尝试用 Scrapling 的选择器查找时间元素
print("\n=== 查找时间元素 ===")
try:
    # 查找包含时间的元素
    time_elements = page.css('*:contains(":")')
    print(f"找到 {len(time_elements)} 个包含:的元素")
    for elem in time_elements[:10]:
        text_content = elem.get_text()
        if re.search(r'\d{1,2}:\d{2}', text_content) and len(text_content) < 100:
            print(f"  {text_content[:80]}")
except Exception as e:
    print(f"选择器查找失败: {e}")

# 查找价格-时间组合
print("\n=== 查找价格附近的时间 ===")
# 查找包含 ¥ 的元素
price_elements = page.css('*:contains("¥")')
print(f"找到 {len(price_elements)} 个包含¥的元素")
for elem in price_elements[:5]:
    text_content = elem.get_text()
    if len(text_content) < 200:
        print(f"  {text_content[:100]}")
