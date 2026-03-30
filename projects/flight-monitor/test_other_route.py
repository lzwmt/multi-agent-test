"""测试其他航线"""
from fetcher_production import FlightFetcher

fetcher = FlightFetcher()

# 测试北京 -> 上海
print("\n" + "="*70)
print("测试航线: 北京 -> 上海")
print("="*70)

result = fetcher.get_complete_data(
    dep_city="北京",
    arr_city="上海",
    dep_code="PEK",
    arr_code="SHA",
    date_str="2026-03-14"
)

print("\n" + "="*70)
print("测试航线: 深圳 -> 成都")
print("="*70)

# 测试深圳 -> 成都
result2 = fetcher.get_complete_data(
    dep_city="深圳",
    arr_city="成都",
    dep_code="SZX",
    arr_code="CTU",
    date_str="2026-03-14"
)
