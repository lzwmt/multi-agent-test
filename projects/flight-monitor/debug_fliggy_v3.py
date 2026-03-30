"""调试飞猪 - 用 Scrapling 抓移动端"""
from scrapling.fetchers import StealthyFetcher
import re

url = "https://s.fliggy.com/mipz/flight-search?tripType=0&depCity=CAN&arrCity=TAO&depDate=2026-03-14"

print("正在抓取飞猪...")
page = StealthyFetcher.fetch(
    url,
    headless=True,
    network_idle=True,
    wait=15000,
)

html = page.css('body').get()
print(f"页面长度: {len(html)}")

# 保存HTML
with open('/tmp/fliggy_scrapling.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 查找价格模式
print("\n查找价格...")

# 方法1: 找 ¥ 后面跟着的数字
prices1 = re.findall(r'[¥¥]\s*([\d,]+)', html)
print(f"方法1 (¥符号): {len(prices1)} 个匹配")

# 方法2: 找 price 字段
prices2 = re.findall(r'["\']price["\']\s*:\s*(\d+)', html)
print(f"方法2 (price字段): {len(prices2)} 个匹配")

# 方法3: 找 data-price
prices3 = re.findall(r'data-price="([\d,]+)"', html)
print(f"方法3 (data-price): {len(prices3)} 个匹配")

# 合并所有价格
all_prices = []
for p in prices1 + prices2 + prices3:
    try:
        price = int(p.replace(',', ''))
        if 100 <= price <= 5000:
            all_prices.append(price)
    except:
        pass

unique_prices = sorted(set(all_prices))
if unique_prices:
    print(f"\n✓ 找到价格: {unique_prices[:10]}")
else:
    print("\n✗ 未找到有效价格")
