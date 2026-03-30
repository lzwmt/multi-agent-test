"""劫持携程API响应获取航班数据"""
import json
import time
from playwright.sync_api import sync_playwright


def hijack_ctrip_api(dep_code, arr_code, date_str):
    """劫持携程API"""
    print(f"\n{'='*70}")
    print(f"劫持携程API: {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    cookies = {
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
    
    api_data = []
    
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
            } for k, v in cookies.items()])
            
            page = context.new_page()
            
            # 劫持响应
            def handle_response(response):
                url = response.url
                
                # 查找航班列表API
                if any(x in url.lower() for x in ['flight', 'search', 'list', 'api']) and response.status == 200:
                    try:
                        data = response.json()
                        data_str = json.dumps(data)
                        
                        # 检查是否包含航班数据
                        if any(x in data_str.lower() for x in ['flightno', 'flightno', 'price', 'depart', 'arrive']):
                            print(f"\n[API] {url[:80]}...")
                            print(f"  数据大小: {len(data_str)} 字节")
                            api_data.append({
                                'url': url,
                                'data': data,
                            })
                            
                            # 保存
                            with open(f'/tmp/ctrip_api_{date_str}.json', 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"  ✓ 已保存")
                    except:
                        pass
            
            page.on('response', handle_response)
            
            # 访问页面
            url = f"https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}"
            print(f"\n访问: {url}")
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(20)  # 等待API调用
            
            browser.close()
            
            # 分析结果
            print(f"\n{'='*70}")
            print(f"劫持到 {len(api_data)} 个API响应")
            print('='*70)
            
            for i, item in enumerate(api_data, 1):
                print(f"\n{i}. {item['url'][:80]}")
                # 简单分析数据结构
                data = item['data']
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            print(f"   {key}: {len(value)} 项")
                        elif isinstance(value, dict):
                            print(f"   {key}: 字典")
            
            return api_data
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    hijack_ctrip_api("CAN", "TAO", "2026-03-14")
