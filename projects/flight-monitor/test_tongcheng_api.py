"""直接调用同程API"""
import requests
import json
import time


def call_tongcheng_api(dep_code, arr_code, date_str):
    """调用同程API"""
    print(f"\n{'='*70}")
    print(f"[同程API] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    # 从劫持获取的API
    url = "https://wx.17u.cn/flightbffv2/book1/preflights"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'application/json',
        'Referer': 'https://m.ly.com/',
        'Origin': 'https://m.ly.com',
    }
    
    params = {
        'dep': dep_code,
        'arr': arr_code,
        'date': date_str,
    }
    
    try:
        time.sleep(1)
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            if data.get('success'):
                flight_data = data.get('data', {})
                
                # 获取最低价格
                lowest_price = flight_data.get('lp', 0)
                
                # 获取价格日历
                price_calendar = flight_data.get('pc', [])
                
                print(f"\n✓ 最低价格: ¥{lowest_price}")
                print(f"✓ 价格日历: {len(price_calendar)} 天")
                
                # 查找指定日期的价格
                for item in price_calendar:
                    if item.get('dd') == date_str:
                        print(f"\n{date_str}:")
                        print(f"  最低: ¥{item.get('lp', 0)}")
                        print(f"  最高: ¥{item.get('hlp', 0)}")
                        # 解析航班信息
                        ms = item.get('ms', '')
                        if ms:
                            parts = ms.split('|')
                            if len(parts) >= 6:
                                print(f"  航班号: {parts[5]}")
                        break
                
                return data
            else:
                print(f"✗ API返回失败: {data}")
        else:
            print(f"✗ 请求失败: {resp.status_code}")
    
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    return None


if __name__ == "__main__":
    call_tongcheng_api("CAN", "TAO", "2026-03-14")
