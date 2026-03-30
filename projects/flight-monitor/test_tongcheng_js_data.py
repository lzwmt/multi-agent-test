"""查找同程页面中的JavaScript数据"""
import re
import json
from playwright.sync_api import sync_playwright


def find_js_data(dep_code, arr_code, date_str):
    """查找页面中的JavaScript数据"""
    print(f"\n{'='*70}")
    print(f"[查找JS数据] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844},
            )
            
            page = context.new_page()
            
            # 访问页面
            url = f"https://m.ly.com/flight/itinerary?dep={dep_code}&arr={arr_code}&date={date_str}"
            print(f"\n访问: {url}")
            
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(10)
            
            # 获取页面HTML
            html = page.content()
            
            # 查找所有script标签
            scripts = page.locator('script').all()
            print(f"\n找到 {len(scripts)} 个script标签")
            
            # 查找包含航班数据的script
            for i, script in enumerate(scripts):
                try:
                    text = script.text_content()
                    if text and len(text) > 1000:  # 大数据量
                        # 检查是否包含航班特征
                        if 'flight' in text.lower() or 'fn' in text or 'SC4673' in text:
                            print(f"\nScript {i}: {len(text)} 字节")
                            
                            # 尝试提取JSON数据
                            json_matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', text, re.DOTALL)
                            if json_matches:
                                print(f"  ✓ 找到 __INITIAL_STATE__")
                                with open(f'/tmp/tongcheng_js_{i}.json', 'w', encoding='utf-8') as f:
                                    f.write(json_matches[0])
                            
                            # 尝试提取其他JSON
                            json_pattern = r'({[\s\S]*?"fn"[\s\S]*?})'
                            matches = re.findall(json_pattern, text)
                            if matches:
                                print(f"  ✓ 找到 {len(matches)} 个可能的JSON对象")
                except:
                    pass
            
            # 执行JavaScript获取数据
            print("\n尝试执行JS获取数据...")
            try:
                # 尝试访问全局变量
                result = page.evaluate('() => { return window.__INITIAL_STATE__; }')
                if result:
                    print(f"✓ 获取到 __INITIAL_STATE__: {type(result)}")
                    with open('/tmp/tongcheng_initial_state.json', 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
            except:
                print("✗ 无法获取 __INITIAL_STATE__")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    find_js_data("CAN", "TAO", "2026-03-14")
