"""生产版航班数据抓取器 - 携程API + 去哪儿 + AirLabs"""
import json
import time
import random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright


class FlightFetcher:
    """生产版航班数据抓取器"""
    
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
    
    def get_ctrip_data(self, dep_code, arr_code, date_str):
        """从携程API获取完整航班数据"""
        print(f"\n[携程] {dep_code} -> {arr_code}, {date_str}")
        
        flights = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080},
                )
                
                context.add_cookies([{
                    'name': k,
                    'value': v,
                    'domain': '.ctrip.com',
                    'path': '/'
                } for k, v in self.ctrip_cookies.items()])
                
                page = context.new_page()
                
                # 劫持响应
                def handle_response(response):
                    url = response.url
                    if 'batchSearch' in url and response.status == 200:
                        try:
                            data = response.json()
                            if 'data' in data and 'flightItineraryList' in data['data']:
                                flights.extend(data['data']['flightItineraryList'])
                        except:
                            pass
                
                page.on('response', handle_response)
                
                # 访问页面
                url = f"https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}"
                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(15)
                
                browser.close()
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        
        # 解析航班数据（只保留直飞）
        results = []
        for flight in flights:
            try:
                segments = flight.get('flightSegments', [])
                if not segments:
                    continue
                
                segment = segments[0]
                
                # 检查是否为直飞（transferCount为0且flightList只有一个航班）
                transfer_count = segment.get('transferCount', 0)
                flight_list = segment.get('flightList', [])
                
                # 过滤条件：直飞（无中转）
                if transfer_count > 0 or len(flight_list) > 1:
                    continue  # 跳过中转航班
                
                if not flight_list:
                    continue
                
                flight_info = flight_list[0]
                price_list = flight.get('priceList', [])
                
                if price_list:
                    price = price_list[0].get('adultPrice', 0)
                else:
                    price = 0
                
                # 获取航空公司名称（优先使用实际承运航司）
                airline = flight_info.get('operateAirlineName') or flight_info.get('marketAirlineName', '')
                
                results.append({
                    'flight_no': flight_info.get('flightNo', ''),
                    'airline': airline,
                    'dep_time': flight_info.get('departureDateTime', ''),
                    'arr_time': flight_info.get('arrivalDateTime', ''),
                    'dep_airport': flight_info.get('departureAirportName', ''),
                    'arr_airport': flight_info.get('arrivalAirportName', ''),
                    'duration': flight_info.get('duration', 0),
                    'price': price,
                })
            except:
                pass
        
        if results:
            print(f"  ✓ 找到 {len(results)} 个航班")
            prices = [f['price'] for f in results if f['price'] > 0]
            if prices:
                print(f"  ✓ 价格范围: ¥{min(prices)} - ¥{max(prices)}")
        
        return results
    
    def get_qunar_price(self, dep_code, arr_code, date_str):
        """从去哪儿获取价格"""
        import requests
        
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
            resp = requests.post(url, headers=headers, cookies=cookies, json=payload, timeout=30)
            
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
    
    def get_tongcheng_price(self, dep_code, arr_code, date_str):
        """从同程获取价格"""
        import requests
        import time as time_module
        
        print(f"\n[同程] {dep_code} -> {arr_code}, {date_str}")
        
        url = "https://wx.17u.cn/flightbffv2/book1/preflights"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://m.ly.com',
            'Referer': 'https://m.ly.com/',
            'tcplat': '10060',
            'tcpolaris': '1',
        }
        
        # 生成sessionid
        timestamp = int(time_module.time() * 1000)
        headers['tcsessionid'] = f"0-{timestamp}"
        headers['tctracerid'] = f"test-{timestamp}"
        
        # 注意：acc和dcc参数名相反
        payload = {
            "acc": dep_code,
            "dcc": arr_code,
            "ddate": date_str,
            "cabin": 0,
            "pt": 0,
            "entrance": 11,
            "pc": {"sd": date_str, "ed": date_str},
            "depAirport": None,
            "arrAirport": None
        }
        
        try:
            time.sleep(random.uniform(1, 2))
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('success'):
                    flight_data = data.get('data', {})
                    
                    # 检查航线
                    if flight_data.get('a') == dep_code and flight_data.get('d') == arr_code:
                        # 从价格日历获取价格
                        for item in flight_data.get('pc', []):
                            if item.get('dd') == date_str:
                                price = item.get('lp', 0)
                                if price > 0:
                                    print(f"  ✓ 价格: ¥{price}")
                                    return price
                        
                        # 返回最低价格
                        lowest = flight_data.get('lp', 0)
                        if lowest > 0:
                            print(f"  ✓ 最低价格: ¥{lowest}")
                            return lowest
                    else:
                        print(f"  ⚠ 航线不匹配")
                else:
                    print(f"  ✗ API失败")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        
        return None
    
    def get_airlabs_schedule(self, dep_code, arr_code, date_str):
        """从AirLabs获取航班时刻"""
        import requests
        
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
        
        # 获取数据
        ctrip_flights = self.get_ctrip_data(dep_code, arr_code, date_str)
        qunar_price = self.get_qunar_price(dep_code, arr_code, date_str)
        tongcheng_price = self.get_tongcheng_price(dep_code, arr_code, date_str)
        
        # 如果携程有完整数据，不调用AirLabs
        if ctrip_flights:
            airlabs_flights = []
            print("\n[AirLabs] 跳过（携程已有完整数据）")
        else:
            airlabs_flights = self.get_airlabs_schedule(dep_code, arr_code, date_str)
        
        # 整合
        result = {
            'date': date_str,
            'route': f"{dep_city} -> {arr_city}",
            'ctrip_flights': ctrip_flights,
            'qunar_price': qunar_price,
            'tongcheng_price': tongcheng_price,
            'airlabs_flights': airlabs_flights,
        }
        
        # 计算最低价格并找到对应航班
        all_prices = []
        lowest_flight = None
        
        for f in ctrip_flights:
            if f['price'] > 0:
                all_prices.append(f['price'])
                if lowest_flight is None or f['price'] < lowest_flight['price']:
                    lowest_flight = f
        
        if qunar_price:
            all_prices.append(qunar_price)
        
        if tongcheng_price:
            all_prices.append(tongcheng_price)
        
        if all_prices:
            result['lowest_price'] = min(all_prices)
            result['highest_price'] = max(all_prices)
            result['lowest_flight'] = lowest_flight
        
        # 输出结果
        print("\n" + "=" * 70)
        print("结果汇总")
        print("=" * 70)
        
        if ctrip_flights:
            ctrip_prices = [f['price'] for f in ctrip_flights if f['price'] > 0]
            if ctrip_prices:
                print(f"携程: ¥{min(ctrip_prices)} - ¥{max(ctrip_prices)} ({len(ctrip_flights)}个直飞航班)")
        
        if qunar_price:
            print(f"去哪儿: ¥{qunar_price}")
        
        if tongcheng_price:
            print(f"同程: ¥{tongcheng_price}")
        
        if all_prices:
            print(f"最低价格: ¥{min(all_prices)}")
        
        # 显示最低价航班详情
        if lowest_flight:
            print(f"\n💰 最低价航班详情:")
            print(f"  航班号: {lowest_flight['flight_no']}")
            print(f"  航空公司: {lowest_flight['airline']}")
            print(f"  起飞: {lowest_flight['dep_time']}")
            print(f"  降落: {lowest_flight['arr_time']}")
            print(f"  出发机场: {lowest_flight['dep_airport']}")
            print(f"  到达机场: {lowest_flight['arr_airport']}")
            print(f"  价格: ¥{lowest_flight['price']}")
        
        return result
    
    def monitor(self, dep_city, arr_city, dep_code, arr_code, days=7, threshold=500):
        """监控价格"""
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
            
            lowest = result.get('lowest_price')
            if lowest and lowest <= threshold:
                alerts.append({
                    'date': date_str,
                    'price': lowest,
                    'message': f"🎉 低价提醒: {dep_city}->{arr_city} {date_str} 价格 ¥{lowest}"
                })
            
            time.sleep(2)
        
        # 报告
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
        
        return results, alerts


if __name__ == "__main__":
    fetcher = FlightFetcher()
    
    # 监控3天
    results, alerts = fetcher.monitor(
        dep_city="广州",
        arr_city="青岛",
        dep_code="CAN",
        arr_code="TAO",
        days=3,
        threshold=1000
    )
