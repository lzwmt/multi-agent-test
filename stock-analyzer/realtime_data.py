#!/usr/bin/env python3
"""
实时股票数据获取模块
支持多个数据源：腾讯、新浪、东方财富
"""

import requests
import json
import time
from datetime import datetime

class RealtimeDataSource:
    """实时数据源"""
    
    @staticmethod
    def tencent_realtime(symbol):
        """
        腾讯财经实时数据
        格式: http://qt.gtimg.cn/q=sh600869
        """
        try:
            # 上海股票加sh，深圳股票加sz
            prefix = 'sh' if symbol.startswith('6') else 'sz'
            url = f'http://qt.gtimg.cn/q={prefix}{symbol}'
            
            response = requests.get(url, timeout=10)
            response.encoding = 'gbk'
            data = response.text
            
            if 'v_' not in data:
                return None, "无数据返回"
            
            # 解析数据
            parts = data.split('~')
            if len(parts) < 40:
                return None, "数据格式错误"
            
            result = {
                'symbol': symbol,
                'name': parts[1],
                'price': float(parts[3]),
                'yesterday_close': float(parts[4]),
                'open': float(parts[5]),
                'volume': int(parts[6]),
                'high': float(parts[33]),
                'low': float(parts[34]),
                'change_pct': float(parts[32]),
                'change_amount': float(parts[31]),
                'quote_time': parts[30],
                'bid1_price': float(parts[9]),
                'bid1_volume': int(parts[10]),
                'ask1_price': float(parts[19]),
                'ask1_volume': int(parts[20]),
                'turnover': float(parts[37]),  # 成交额
                'source': 'tencent',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return result, "成功"
            
        except Exception as e:
            return None, f"腾讯API错误: {str(e)}"
    
    @staticmethod
    def sina_realtime(symbol):
        """
        新浪财经实时数据
        格式: https://hq.sinajs.cn/list=sh600869
        """
        try:
            prefix = 'sh' if symbol.startswith('6') else 'sz'
            url = f'https://hq.sinajs.cn/list={prefix}{symbol}'
            
            headers = {
                'Referer': 'https://finance.sina.com.cn'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'gb2312'
            data = response.text
            
            if 'var hq_str_' not in data:
                return None, "无数据返回"
            
            # 解析数据
            # 格式: var hq_str_sh600869="远东股份,13.450,13.600,13.770..."
            start = data.find('"') + 1
            end = data.rfind('"')
            values = data[start:end].split(',')
            
            if len(values) < 30:
                return None, "数据格式错误"
            
            result = {
                'symbol': symbol,
                'name': values[0],
                'open': float(values[1]),
                'yesterday_close': float(values[2]),
                'price': float(values[3]),
                'high': float(values[4]),
                'low': float(values[5]),
                'volume': int(values[8]),
                'amount': float(values[9]),
                'bid1_volume': int(values[10]),
                'bid1_price': float(values[11]),
                'ask1_volume': int(values[20]),
                'ask1_price': float(values[21]),
                'date': values[30],
                'time': values[31],
                'source': 'sina',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 计算涨跌幅
            result['change_pct'] = round((result['price'] - result['yesterday_close']) / result['yesterday_close'] * 100, 2)
            
            return result, "成功"
            
        except Exception as e:
            return None, f"新浪API错误: {str(e)}"
    
    @staticmethod
    def get_realtime(symbol, prefer='tencent'):
        """
        获取实时数据（自动选择数据源）
        """
        sources = {
            'tencent': RealtimeDataSource.tencent_realtime,
            'sina': RealtimeDataSource.sina_realtime
        }
        
        # 优先使用指定源
        if prefer in sources:
            result, msg = sources[prefer](symbol)
            if result:
                return result, msg
        
        # 失败后尝试其他源
        for name, func in sources.items():
            if name != prefer:
                result, msg = func(symbol)
                if result:
                    return result, msg
        
        return None, "所有数据源均失败"
    
    @staticmethod
    def get_batch_realtime(symbols, prefer='tencent'):
        """
        批量获取实时数据
        """
        results = []
        for symbol in symbols:
            result, msg = RealtimeDataSource.get_realtime(symbol, prefer)
            if result:
                results.append(result)
            else:
                print(f"获取 {symbol} 失败: {msg}")
            time.sleep(0.1)  # 避免请求过快
        return results


# 测试
if __name__ == "__main__":
    import sys
    
    symbol = sys.argv[1] if len(sys.argv) > 1 else '600869'
    
    print(f"查询股票 {symbol} 实时数据...\n")
    
    # 腾讯
    print("=" * 50)
    print("腾讯财经:")
    result, msg = RealtimeDataSource.tencent_realtime(symbol)
    if result:
        print(f"名称: {result['name']}")
        print(f"价格: ¥{result['price']}")
        print(f"涨跌: {result['change_pct']}%")
        print(f"成交量: {result['volume']}")
        print(f"时间: {result['quote_time']}")
    else:
        print(f"失败: {msg}")
    
    # 新浪
    print("\n" + "=" * 50)
    print("新浪财经:")
    result, msg = RealtimeDataSource.sina_realtime(symbol)
    if result:
        print(f"名称: {result['name']}")
        print(f"价格: ¥{result['price']}")
        print(f"涨跌: {result['change_pct']}%")
        print(f"成交量: {result['volume']}")
        print(f"时间: {result['date']} {result['time']}")
    else:
        print(f"失败: {msg}")
