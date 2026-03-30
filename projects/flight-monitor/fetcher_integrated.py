"""整合版航班数据抓取器 - 携程为主 + 去哪儿价格参考"""
import requests
import json
import time
import random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright


class FlightFetcher:
    """航班数据抓取器"""
    
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
    
    def get_ctrip_flights(self, dep_city, arr_city, date_str):
        """从携程获取航班数据"""
        print(f"\n[携程] {dep_city} -> {arr_city}, {date_str}")
        
        flights = []
        
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
                
                # 访问携程航班页面
                url = f"https://flights.ctrip.com/online/channel/domestic"
                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(5)
                
                # 这里简化处理，实际应该填写表单并搜索
                # 由于携程页面复杂，这里使用模拟数据演示结构
                
                browser.close()
                
        except Exception as e:
            print(f"  ✗ 携程抓取失败: {e}")
        
        return flights
    
    def get_qunar_price(self, dep_code, arr_code, date_str):
        """从去哪儿获取价格（仅价格）"""
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
                else:
                    print(f"  ⚠ 无价格数据")
            else:
                print(f"  ✗ 请求失败: {resp.status_code}")
        
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
                
                # 提取关键信息
                results = []
                for flight in flights[:5]:
                    results.append({
                        'flight_no': flight.get('flight_iata', ''),
                        'dep_time': flight.get('dep_time', ''),
                        'arr_time': flight.get('arr_time', ''),
                        'airline': flight.get('airline_iata', ''),
                    })
                
                return results
            else:
                print(f"  ✗ 请求失败: {resp.status_code}")
        
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        
        return []
    
    def get_integrated_data(self, dep_city, arr_city, dep_code, arr_code, date_str):
        """获取整合数据"""
        print("=" * 70)
        print(f"整合数据: {dep_city}({dep_code}) -> {arr_city}({arr_code}), {date_str}")
        print("=" * 70)
        
        # 1. 获取去哪儿价格
        qunar_price = self.get_qunar_price(dep_code, arr_code, date_str)
        
        # 2. 获取AirLabs航班时刻
        airlabs_flights = self.get_airlabs_schedule(dep_code, arr_code, date_str)
        
        # 3. 整合数据
        result = {
            'date': date_str,
            'route': f"{dep_city} -> {arr_city}",
            'qunar_price': qunar_price,
            'flights': airlabs_flights,
        }
        
        print("\n" + "=" * 70)
        print("整合结果")
        print("=" * 70)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result


if __name__ == "__main__":
    fetcher = FlightFetcher()
    
    # 测试广州 -> 青岛
    result = fetcher.get_integrated_data(
        dep_city="广州",
        arr_city="青岛",
        dep_code="CAN",
        arr_code="TAO",
        date_str="2026-03-14"
    )
