"""正确提取携程价格"""
import re
import time
from playwright.sync_api import sync_playwright


def get_ctrip_correct(dep_code, arr_code, date_str):
    """正确提取携程价格"""
    print(f"\n{'='*70}")
    print(f"携程正确提取: {dep_code} -> {arr_code}, {date_str}")
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
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 等待航班列表加载
            print("等待航班列表加载...")
            time.sleep(15)
            
            # 截图查看
            page.screenshot(path=f'/tmp/ctrip_correct_{date_str}.png', full_page=True)
            print(f"✓ 截图已保存")
            
            # 获取HTML
            html = page.content()
            
            # 查找航班列表区域
            print("\n查找航班数据...")
            
            # 查找包含航班信息的脚本
            scripts = page.locator('script').all()
            for script in scripts:
                try:
                    text = script.text_content()
                    if text and ('flight' in text.lower() or 'price' in text.lower()):
                        if len(text) > 1000:
                            print(f"  找到大脚本: {len(text)} 字节")
                            # 查找价格模式
                            prices = re.findall(r'"price":\s*([\d]+)', text)
                            if prices:
                                print(f"  脚本中的价格: {prices[:10]}")
                except:
                    pass
            
            # 使用选择器查找价格元素
            print("\n使用选择器查找价格...")
            price_selectors = [
                '.flight-price',
                '.price',
                '[class*="price"]',
                '.flight-item .price',
            ]
            
            for selector in price_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        print(f"\n  选择器 '{selector}' 找到 {len(elements)} 个元素")
                        for elem in elements[:5]:
                            text = elem.text_content()
                            print(f"    {text[:50]}")
                except Exception as e:
                    print(f"  选择器 '{selector}' 失败: {e}")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    get_ctrip_correct("CAN", "TAO", "2026-03-14")
