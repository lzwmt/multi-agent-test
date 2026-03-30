"""测试抓取可行性"""
import subprocess
import sys
from datetime import datetime, timedelta

# 测试 Skyscanner
def test_skyscanner():
    """测试 Skyscanner 抓取"""
    # Skyscanner URL 格式示例
    # https://www.skyscanner.com/transport/flights/can/tao/250411/250412/?adults=1&adultsv2=1&cabinclass=economy

    # 构建未来某天的 URL
    future_date = (datetime.now() + timedelta(days=7)).strftime("%y%m%d")
    url = f"https://www.skyscanner.com/transport/flights/can/tao/{future_date}/?adults=1&cabinclass=economy"

    print(f"测试 Skyscanner: {url}")

    # 使用 scrapling 抓取
    cmd = [
        "bash", "-c",
        f"source ~/.venvs/scrapling/bin/activate && scrapling extract stealthy-fetch '{url}' /tmp/skyscanner_test.md --headless --network-idle --wait 3000"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(f"返回码: {result.returncode}")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")

    # 读取结果
    try:
        with open("/tmp/skyscanner_test.md", "r") as f:
            content = f.read()
            print(f"内容长度: {len(content)} 字符")
            print("前1000字符预览:")
            print(content[:1000])
            return content
    except FileNotFoundError:
        print("未生成输出文件")
        return None

# 测试 Trip.com
def test_trip():
    """测试 Trip.com 抓取"""
    # Trip.com URL 格式
    # https://www.trip.com/flights/can-to-tao/departure-2025-04-11/?adult=1&cabin=0

    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://www.trip.com/flights/can-to-tao/departure-{future_date}/?adult=1&cabin=0"

    print(f"\n测试 Trip.com: {url}")

    cmd = [
        "bash", "-c",
        f"source ~/.venvs/scrapling/bin/activate && scrapling extract stealthy-fetch '{url}' /tmp/trip_test.md --headless --network-idle --wait 3000"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(f"返回码: {result.returncode}")

    try:
        with open("/tmp/trip_test.md", "r") as f:
            content = f.read()
            print(f"内容长度: {len(content)} 字符")
            print("前1000字符预览:")
            print(content[:1000])
            return content
    except FileNotFoundError:
        print("未生成输出文件")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("开始测试机票网站抓取")
    print("=" * 50)

    # 测试 Skyscanner
    sky_content = test_skyscanner()

    # 测试 Trip.com
    trip_content = test_trip()

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
