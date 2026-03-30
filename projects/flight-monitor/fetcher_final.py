"""最终版航班数据抓取器 - 完整功能"""
import requests
import json
import time
import random
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright


class FlightFetcher:
    """最终版航班数据抓取器"""
    
    def __init__(self):
        self.ctrip_cookies = self._load_ctrip_cookies()
        self.airlabs_api_key = "3ad12eb5-3908-4c16-a844-343af49a3ea2"
        
    def _load_ctrip_cookies(self):
        """加载携程Cookie"""
        return {
            '_bfa': '1.1773298447354.d448XhhHBfUO.1.1773298537519.1773298553036.1.10.102001',
            '_ga': 'GA1.1.804476880.1773298553',
            'GUID': '09031036416118655147',
            'DUID': 'u=3DFF547364985F3DEB3090547473BF20&v=0',
            'cticket': '05ADD5CC9E616FF981FDAF4AC031B5C1CA4E7BB33775BBBAF8156059A9DE675D',
            '_udl': '708D70C2B179E2F91CC5ED1C2CCE362D',
            'login_uid': '81691936B6783FD74467BB5E689E059B',
            'login_type': '0',
            'IsNonUser': 'F',
            'UBT_VID': '1773298447354.d448XhhHBfUO',
            '_RGUID': '4e3823cf-2bda-476c-8658-0c6b5a12cda2',
        }
    
    def get_ctrip_price(self, dep_code, arr_code, date_str):
        """从携程获取价格 - 使用Cookie登录"""
        print(f"\n[携程] {dep_code} -> {arr_code}, {date_str}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080},
                )
                
                # 添加Cookie
                context.add_cookies([{
                    'name': k,
                    'value': v,
                    'domain': '.ctrip.com',
                    'path': '/'
                } for k, v in self.ctrip_cookies.items()])
                
                page = context.new_page()
                
                # 访问携程航班搜索页
                url = f"https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}&cabin=Y_S_C_F"
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                time.sleep(8)
                
                # 等待价格加载
                try:
                    page.wait_for_selector('.flight-price, .price, [class*="price"]', timeout=10000)
                except:
                    pass
                
                time.sleep(3)
                
                # 提取价格
                html = page.content()
                
                # 多种价格模式
                prices = []
                prices.extend(re.findall(r'¥\s*([\d,]+)', html))
                prices.extend(re.findall(r'"price":\s*([\d]+)', html))
                prices.extend(re.findall(r'data-price="([\d]+)"', html))
                
                # 过滤有效价格
                valid_prices = []
                for p in prices:
                    try:
                        price_val = int(p.replace(',', ''))
                        if 200 <= price_val <= 5000:
                            valid_prices.append(price_val)
                    except:
                        pass
                
                # 提取航班号
                flight_nos = re.findall(r'([A-Z]{2}\d{3,4})', html)
                
                browser.close()
                
                if valid_prices:
                    print(f"  ✓ 价格范围: ¥{min(valid_prices)} - ¥{max(valid_prices)}")
                    return {
                        'min_price': min(valid_prices),
                        'max_price': max(valid_prices),
                        'all_prices': sorted(set(valid_prices)),
                        'flight_nos': list(set(flight_nos))[:10],
                    }
                else:
                    print(f"  ⚠ 未找到价格")
        
        except Exception as e:
            print(f"  ✗ 携程抓取失败: {e}")
        
        return None
    
    def get_qunar_price(self, dep_code, arr_code, date_str):
        """从去哪儿获取价格"""
        print(f"\n[去哪儿] {dep_code} -> {arr_code}, {date_str}")
        
        url = "https://m.flight.qunar.com/lowFlightInterface/api/getAsyncPrice"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json; charset=UTF-8',
            'Origin': 'https://m.flight.qunar.com',
            'Referer': 'https://m.flight.qunar.com/h5/flight/',
        }
        
        cookies = {
            'QN1': '000197802f107b496f80bb26',
            'QN48': '000197802f107b496f80bb26',
            'Alina': 'c2440aac-c15f39-944f9e15-838fdb77-28b669b2a7f2',
        }
        
        flight_code = f"{dep_code}_{arr_code}_{date_str}"
        
        payload = {
            "b": {
                "timeout": 5000,
                "simpleData": "yes",
                "t": "f_urInfo_superLow_async",
                "flightInfo": [{"flightCode": flight_code, "price": "", "jumpUrl": ""}]
            }
        }
        
        try:
            time.sleep(random.uniform(1, 2))
            
            resp = requests.post(
                url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=30,
            )
            
            if resp.status_code == 200:
                data = resp.json()
                result = data.get('data', {}).get('asyncResultMap', {}).get(flight_code, {})
                price = result.get('price', '')
                
                if price:
                    print(f"  ✓ 价格: ¥{price}")
                    return int(price)
        
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        
        return None
    
    def get_airlabs_schedule(self, dep_code, arr_code, date_str):
        """从AirLabs获取航班时刻表"""
        print(f"\n[AirLabs] {dep_code} -> {arr_code}, {date_str}")
        
        url = "https://airlabs.co/api/v9/schedules"
        
        params = {
            'api_key': self.airlabs_api_key,
            'dep_iata': dep_code,
            'arr_iata': arr_code,
            'date': date_str,
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                flights = data.get('response', [])
                
                print(f"  ✓ 找到 {len(flights)} 个航班")
                
                results = []
                for flight in flights[:5]:
                    results.append({
                        'flight_no': flight.get('flight_iata', ''),
                        'dep_time': flight.get('dep_time', ''),
                        'arr_time': flight.get('arr_time', ''),
                        'airline': flight.get('airline_iata', ''),
                    })
                
                return results
        
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        
        return []
    
    def get_complete_data(self, dep_city, arr_city, dep_code, arr_code, date_str):
        """获取完整数据"""
        print("=" * 70)
        print(f"完整数据: {dep_city}({dep_code}) -> {arr_city}({arr_code}), {date_str}")
        print("=" * 70)
        
        # 1. 携程价格
        ctrip_data = self.get_ctrip_price(dep_code, arr_code, date_str)
        
        # 2. 去哪儿价格
        qunar_price = self.get_qunar_price(dep_code, arr_code, date_str)
        
        # 3. AirLabs航班时刻
        airlabs_flights = self.get_airlabs_schedule(dep_code, arr_code, date_str)
        
        # 4. 整合数据
        result = {
            'date': date_str,
            'route': f"{dep_city} -> {arr_city}",
            'prices': {
                'ctrip': ctrip_data,
                'qunar': qunar_price,
            },
            'flights': airlabs_flights,
        }
        
        # 5. 计算最低价格
        all_prices = []
        if ctrip_data and 'min_price' in ctrip_data:
            all_prices.append(ctrip_data['min_price'])
        if qunar_price:
            all_prices.append(qunar_price)
        
        if all_prices:
            result['lowest_price'] = min(all_prices)
            result['highest_price'] = max(all_prices)
        
        print("\n" + "=" * 70)
        print("结果汇总")
        print("=" * 70)
        
        if ctrip_data:
            print(f"携程: ¥{ctrip_data['min_price']} - ¥{ctrip_data['max_price']}")
        else:
            print("携程: 无数据")
        
        if qunar_price:
            print(f"去哪儿: ¥{qunar_price}")
        else:
            print("去哪儿: 无数据")
        
        if all_prices:
            print(f"最低价格: ¥{min(all_prices)}")
        
        print(f"航班数: {len(airlabs_flights)}")
        
        return result
    
    def monitor_prices(self, dep_city, arr_city, dep_code, arr_code, days=7, threshold=500):
        """监控价格并返回告警信息"""
        print("=" * 70)
        print(f"价格监控: {dep_city} -> {arr_city} (阈值: ¥{threshold})")
        print("=" * 70)
        
        base_date = datetime.now()
        results = []
        alerts = []
        
        for i in range(days):
            date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            result = self.get_complete_data(dep_city, arr_city, dep_code, arr_code, date_str)
            results.append(result)
            
            # 检查是否低于阈值
            lowest = result.get('lowest_price')
            if lowest and lowest <= threshold:
                alerts.append({
                    'date': date_str,
                    'price': lowest,
                    'message': f"🎉 发现低价！{dep_city}->{arr_city} {date_str} 价格 ¥{lowest} (低于阈值 ¥{threshold})"
                })
            
            time.sleep(2)
        
        # 汇总报告
        print("\n" + "=" * 70)
        print("监控报告")
        print("=" * 70)
        
        for r in results:
            date = r['date']
            lowest = r.get('lowest_price', 'N/A')
            print(f"{date}: ¥{lowest}")
        
        if alerts:
            print("\n🚨 价格告警:")
            for alert in alerts:
                print(f"  {alert['message']}")
        else:
            print("\n✅ 未发现低于阈值的价格")
        
        return results, alerts


if __name__ == "__main__":
    fetcher = FlightFetcher()
    
    # 测试价格监控（阈值 ¥500）
    results, alerts = fetcher.monitor_prices(
        dep_city="广州",
        arr_city="青岛",
        dep_code="CAN",
        arr_code="TAO",
        days=3,
        threshold=500
    )
