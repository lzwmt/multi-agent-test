"""最终版航班数据抓取器 - 完整功能"""
import json
import time
import random
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
    
    def get_ctrip_data(self, dep_code, arr_code, date_str):
        """从携程获取数据"""
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
                    'name': k, 'value': v, 'domain': '.ctrip.com', 'path': '/'
                } for k, v in self.ctrip_cookies.items()])
                
                page = context.new_page()
                
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
                
                url = f"https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}"
                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(15)
                
                browser.close()
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        
        # 解析数据
        results = []
        for flight in flights:
            try:
                segments = flight.get('flightSegments', [])
                if not segments:
                    continue
                
                segment = segments[0]
                transfer_count = segment.get('transferCount', 0)
                flight_list = segment.get('flightList', [])
                
                if transfer_count > 0 or len(flight_list) > 1:
                    continue
                
                if not flight_list:
                    continue
                
                flight_info = flight_list[0]
                price_list = flight.get('priceList', [])
                price = price_list[0].get('adultPrice', 0) if price_list else 0
                
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
            print(f"  ✓ 找到 {len(results)} 个直飞航班")
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
    
    def get_tongcheng_data(self, dep_code, arr_code, date_str):
        """从同程获取完整数据"""
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
        
        timestamp = int(time_module.time() * 1000)
        headers['tcsessionid'] = f"0-{timestamp}"
        headers['tctracerid'] = f"test-{timestamp}"
        
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
                    
                    if flight_data.get('a') == dep_code and flight_data.get('d') == arr_code:
                        # 获取航班列表
                        flights = flight_data.get('fl', [])
                        
                        # 过滤直飞航班 (nos="1")
                        direct_flights = []
                        for f in flights:
                            if f.get('nos') == '1':
                                direct_flights.append({
                                    'flight_no': f.get('fn', ''),
                                    'airline': f.get('asn', ''),
                                    'dep_time': f.get('dt', ''),
                                    'arr_time': f.get('at', ''),
                                    'dep_airport': f.get('aasn', ''),
                                    'arr_airport': f.get('dasn', ''),
                                    'duration': f.get('td', ''),
                                })
                        
                        # 获取最低价格
                        low_price = flight_data.get('lowPrice', {})
                        min_price = low_price.get('minTicketPrice', {}).get('price', 0) if low_price else 0
                        
                        print(f"  ✓ 找到 {len(direct_flights)} 个直飞航班")
                        if min_price > 0:
                            print(f"  ✓ 最低价格: ¥{min_price}")
                        
                        return {
                            'flights': direct_flights,
                            'min_price': min_price,
                        }
                    else:
                        print(f"  ⚠ 航线不匹配")
                else:
                    print(f"  ✗ API失败")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        
        return None
    
    def get_complete_data(self, dep_city, arr_city, dep_code, arr_code, date_str):
        """获取完整数据"""
        print("=" * 70)
        print(f"完整数据: {dep_city}({dep_code}) -> {arr_city}({arr_code}), {date_str}")
        print("=" * 70)
        
        # 获取数据
        ctrip_flights = self.get_ctrip_data(dep_code, arr_code, date_str)
        qunar_price = self.get_qunar_price(dep_code, arr_code, date_str)
        tongcheng_data = self.get_tongcheng_data(dep_code, arr_code, date_str)
        
        # 整合
        result = {
            'date': date_str,
            'route': f"{dep_city} -> {arr_city}",
            'ctrip_flights': ctrip_flights,
            'qunar_price': qunar_price,
            'tongcheng_data': tongcheng_data,
        }
        
        # 计算最低价格
        all_prices = []
        lowest_flight = None
        
        for f in ctrip_flights:
            if f['price'] > 0:
                all_prices.append(f['price'])
                if lowest_flight is None or f['price'] < lowest_flight['price']:
                    lowest_flight = f
        
        if qunar_price:
            all_prices.append(qunar_price)
        
        if tongcheng_data and tongcheng_data['min_price'] > 0:
            all_prices.append(tongcheng_data['min_price'])
        
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
                print(f"携程: ¥{min(ctrip_prices)} - ¥{max(ctrip_prices)} ({len(ctrip_flights)}个直飞)")
        
        if qunar_price:
            print(f"去哪儿: ¥{qunar_price}")
        
        if tongcheng_data:
            print(f"同程: ¥{tongcheng_data['min_price']} ({len(tongcheng_data['flights'])}个直飞)")
        
        if all_prices:
            print(f"最低价格: ¥{min(all_prices)}")
        
        if lowest_flight:
            print(f"\n💰 最低价航班:")
            print(f"  {lowest_flight['flight_no']} {lowest_flight['airline']}")
            print(f"  {lowest_flight['dep_time']} -> {lowest_flight['arr_time']}")
            print(f"  ¥{lowest_flight['price']}")
        
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
        threshold=600
    )
