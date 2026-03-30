"""检查同程数据结构"""
import json

data = json.load(open('/tmp/tongcheng_pt0.json'))
flight_data = data['data']

print("=== 同程数据结构检查 ===\n")

# 检查所有字段
print("所有字段:")
for key in sorted(flight_data.keys()):
    value = flight_data[key]
    if isinstance(value, list):
        print(f"  {key}: 列表({len(value)}项)")
    elif isinstance(value, dict):
        print(f"  {key}: 字典")
    else:
        print(f"  {key}: {type(value).__name__} = {value}")

print("\n=== 检查fl字段详情 ===")
flights = flight_data.get('fl', [])
print(f"总航班数: {len(flights)}")

# 检查前3个航班
for i, f in enumerate(flights[:3]):
    print(f"\n航班 {i+1}:")
    print(f"  航班号: {f.get('fn')}")
    print(f"  航空公司: {f.get('asn')} ({f.get('ac')})")
    print(f"  起飞: {f.get('dt')}")
    print(f"  降落: {f.get('at')}")
    print(f"  出发机场: {f.get('aasn')} ({f.get('aac')})")
    print(f"  到达机场: {f.get('dasn')} ({f.get('dac')})")
    print(f"  经停次数: {f.get('nos')}")
    print(f"  是否有价格: {f.get('p') is not None}")

print("\n=== 检查价格信息 ===")
low_price = flight_data.get('lowPrice', {})
print(f"lowPrice字段: {list(low_price.keys())}")
if 'minTicketPrice' in low_price:
    mtp = low_price['minTicketPrice']
    print(f"\n最低价格航班:")
    print(f"  航班号: {mtp.get('fn')}")
    print(f"  价格: ¥{mtp.get('price')}")
    print(f"  时间: {mtp.get('dd')}")
