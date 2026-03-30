"""AirLabs API 模块 - 获取航班时间信息"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

API_KEY = "3ad12eb5-3908-4c16-a844-343af49a3ea2"
BASE_URL = "https://airlabs.co/api/v9"
CACHE_FILE = "/tmp/airlabs_cache.json"


class AirLabsClient:
    """AirLabs API 客户端"""
    
    def __init__(self):
        self.api_key = API_KEY
        self.cache = self._load_cache()
        self.request_count = 0
    
    def _load_cache(self) -> Dict:
        """加载缓存"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cache(self):
        """保存缓存"""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"缓存保存失败: {e}")
    
    def _get_cache_key(self, origin: str, dest: str, date: str) -> str:
        """生成缓存键"""
        return f"{origin}-{dest}-{date}"
    
    def get_schedules(self, origin: str, dest: str, date: str) -> List[Dict]:
        """
        获取航班时刻表
        
        Args:
            origin: 出发机场 IATA 代码
            dest: 到达机场 IATA 代码
            date: 日期 (YYYY-MM-DD)
        
        Returns:
            航班列表
        """
        cache_key = self._get_cache_key(origin, dest, date)
        
        # 检查缓存
        if cache_key in self.cache:
            cached_time = self.cache[cache_key].get('cached_at', '')
            if cached_time:
                cached_dt = datetime.fromisoformat(cached_time)
                # 缓存 24 小时
                if datetime.now() - cached_dt < timedelta(hours=24):
                    print(f"  [AirLabs] 使用缓存: {cache_key}")
                    return self.cache[cache_key]['flights']
        
        # 调用 API
        url = f"{BASE_URL}/schedules"
        params = {
            'api_key': self.api_key,
            'dep_iata': origin,
            'arr_iata': dest,
            'date': date,
        }
        
        try:
            print(f"  [AirLabs] 查询 API: {origin}->{dest} {date}")
            resp = requests.get(url, params=params, timeout=30)
            self.request_count += 1
            
            if resp.status_code == 200:
                data = resp.json()
                
                if 'response' in data:
                    flights = data['response']
                    
                    # 简化数据
                    simplified = []
                    for f in flights:
                        simplified.append({
                            'flight_iata': f.get('flight_iata', 'N/A'),
                            'flight_number': f.get('flight_number', 'N/A'),
                            'airline_iata': f.get('airline_iata', 'N/A'),
                            'dep_time': f.get('dep_time', 'N/A'),
                            'arr_time': f.get('arr_time', 'N/A'),
                            'dep_terminal': f.get('dep_terminal', ''),
                            'arr_terminal': f.get('arr_terminal', ''),
                            'duration': f.get('duration', 0),
                            'status': f.get('status', ''),
                        })
                    
                    # 保存到缓存
                    self.cache[cache_key] = {
                        'flights': simplified,
                        'cached_at': datetime.now().isoformat(),
                        'total': len(simplified),
                    }
                    self._save_cache()
                    
                    print(f"  [AirLabs] 获取到 {len(simplified)} 个航班")
                    return simplified
                else:
                    print(f"  [AirLabs] 无航班数据")
                    return []
            else:
                print(f"  [AirLabs] API 错误: {resp.status_code}")
                return []
        
        except Exception as e:
            print(f"  [AirLabs] 请求失败: {e}")
            return []
    
    def get_routes(self, origin: str, dest: str) -> List[Dict]:
        """
        获取航线信息（常规航班）
        
        Args:
            origin: 出发机场 IATA 代码
            dest: 到达机场 IATA 代码
        
        Returns:
            航线列表
        """
        cache_key = f"routes-{origin}-{dest}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached_time = self.cache[cache_key].get('cached_at', '')
            if cached_time:
                cached_dt = datetime.fromisoformat(cached_time)
                # 缓存 7 天
                if datetime.now() - cached_dt < timedelta(days=7):
                    print(f"  [AirLabs] 使用缓存: {cache_key}")
                    return self.cache[cache_key]['routes']
        
        # 调用 API
        url = f"{BASE_URL}/routes"
        params = {
            'api_key': self.api_key,
            'dep_iata': origin,
            'arr_iata': dest,
        }
        
        try:
            print(f"  [AirLabs] 查询航线: {origin}->{dest}")
            resp = requests.get(url, params=params, timeout=30)
            self.request_count += 1
            
            if resp.status_code == 200:
                data = resp.json()
                
                if 'response' in data:
                    routes = data['response']
                    
                    # 简化数据
                    simplified = []
                    for r in routes:
                        simplified.append({
                            'flight_iata': r.get('flight_iata', 'N/A'),
                            'flight_number': r.get('flight_number', 'N/A'),
                            'airline_iata': r.get('airline_iata', 'N/A'),
                            'dep_time': r.get('dep_time', 'N/A'),
                            'arr_time': r.get('arr_time', 'N/A'),
                            'duration': r.get('duration', 0),
                            'days': r.get('days', []),
                        })
                    
                    # 保存到缓存
                    self.cache[cache_key] = {
                        'routes': simplified,
                        'cached_at': datetime.now().isoformat(),
                        'total': len(simplified),
                    }
                    self._save_cache()
                    
                    print(f"  [AirLabs] 获取到 {len(simplified)} 条航线")
                    return simplified
                else:
                    return []
            else:
                print(f"  [AirLabs] API 错误: {resp.status_code}")
                return []
        
        except Exception as e:
            print(f"  [AirLabs] 请求失败: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """获取 API 使用统计"""
        return {
            'request_count': self.request_count,
            'cache_size': len(self.cache),
        }


if __name__ == "__main__":
    # 测试
    client = AirLabsClient()
    
    print("=" * 60)
    print("AirLabs API 测试")
    print("=" * 60)
    
    # 测试航线查询
    print("\n1. 查询航线 (CAN->TAO):")
    routes = client.get_routes('CAN', 'TAO')
    for r in routes[:3]:
        print(f"  {r['flight_iata']}: {r['dep_time']} -> {r['arr_time']}")
    
    # 测试时刻表查询
    print("\n2. 查询时刻表 (2026-03-14):")
    today = datetime.now().strftime('%Y-%m-%d')
    schedules = client.get_schedules('CAN', 'TAO', today)
    for s in schedules[:3]:
        print(f"  {s['flight_iata']}: {s['dep_time']} -> {s['arr_time']} ({s['status']})")
    
    # 统计
    stats = client.get_stats()
    print(f"\n3. API 统计:")
    print(f"  请求次数: {stats['request_count']}")
    print(f"  缓存条目: {stats['cache_size']}")
