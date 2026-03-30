"""携程数据排查"""
import re
import time
from playwright.sync_api import sync_playwright


def debug_ctrip(dep_code, arr_code, date_str):
    """调试携程抓取"""
    print(f"\n{'='*70}")
    print(f"携程调试: {dep_code} -> {arr_code}, {date_str}")
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
            
            # 访问页面
            url = f"https://flights.ctrip.com/online/list/oneway-{dep_code}-{arr_code}?depdate={date_str}&cabin=Y_S_C_F"
            print(f"\n访问: {url}")
            
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(10)
            
            # 截图查看
            page.screenshot(path=f'/tmp/ctrip_debug_{date_str}.png', full_page=True)
            print(f"✓ 截图已保存: /tmp/ctrip_debug_{date_str}.png")
            
            # 获取HTML
            html = page.content()
            
            # 保存HTML
            with open(f'/tmp/ctrip_debug_{date_str}.html', 'w', encoding='utf-8') as f:
                f.write(html[:100000])  # 保存前10万字符
            print(f"✓ HTML已保存: /tmp/ctrip_debug_{date_str}.html")
            
            # 分析价格
            print("\n价格分析:")
            
            # 所有价格模式
            patterns = [
                (r'¥\s*([\d,]+)', '¥符号价格'),
                (r'"price":\s*"?([\d]+)"?', 'JSON price字段'),
                (r'data-price="([\d]+)"', 'data-price属性'),
                (r'class=["\'][^"\']*price[^"\']*["\'][^>]*>([^<]+)', 'price类文本'),
                (r'([\d]{3,4})[^\d]', '3-4位数字'),
            ]
            
            all_prices = []
            for pattern, desc in patterns:
                matches = re.findall(pattern, html)
                if matches:
                    print(f"\n  {desc}:")
                    for m in matches[:10]:
                        try:
                            price = int(m.replace(',', ''))
                            if 200 <= price <= 5000:
                                print(f"    ¥{price}")
                                all_prices.append(price)
                        except:
                            pass
            
            # 去重排序
            unique_prices = sorted(set(all_prices))
            print(f"\n所有有效价格: {unique_prices[:20]}")
            
            # 查找航班信息
            print("\n航班信息:")
            flight_nos = re.findall(r'([A-Z]{2}\d{3,4})', html)
            unique_flights = list(set(flight_nos))
            print(f"  航班号: {unique_flights[:10]}")
            
            # 查找包含价格和航班的文本
            print("\n价格相关文本片段:")
            for line in html.split('\n'):
                if '¥' in line and any(f in line for f in unique_flights[:5]):
                    clean_line = re.sub(r'<[^>]+>', '', line).strip()
                    if clean_line and len(clean_line) < 200:
                        print(f"  {clean_line[:100]}")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_ctrip("CAN", "TAO", "2026-03-14")
