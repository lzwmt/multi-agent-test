"""检查同程页面中的Unicode编码"""
import re
from playwright.sync_api import sync_playwright


def check_unicode_in_page(dep_code, arr_code, date_str):
    """检查页面中的Unicode编码"""
    print(f"\n{'='*70}")
    print(f"[检查Unicode编码] {dep_code} -> {arr_code}, {date_str}")
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
            
            # 获取HTML
            html = page.content()
            
            # 查找Unicode编码 (&#x...; 或 \u...)
            print("\n查找Unicode编码...")
            
            # 查找HTML实体编码
            html_entities = re.findall(r'&#x([0-9a-fA-F]+);', html)
            if html_entities:
                print(f"\n找到 {len(html_entities)} 个HTML实体编码:")
                unique = sorted(set(html_entities))[:20]
                for code in unique:
                    try:
                        char = chr(int(code, 16))
                        print(f"  &#x{code}; -> {char!r}")
                    except:
                        print(f"  &#x{code}; -> (无法转换)")
            
            # 查找CSS中的font-family
            font_families = re.findall(r'font-family:\s*["\']?([^"\'>;]+)["\']?', html)
            if font_families:
                print(f"\n字体定义:")
                for ff in set(font_families):
                    print(f"  {ff}")
            
            # 查找可能的航班号区域
            print("\n查找航班号相关文本...")
            text = page.inner_text('body')
            lines = text.split('\n')
            for line in lines:
                if any(x in line for x in ['航班', 'flight', 'SC', 'CZ', 'MU', 'CA']):
                    if len(line) < 100:
                        print(f"  {line[:80]}")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_unicode_in_page("CAN", "TAO", "2026-03-14")
