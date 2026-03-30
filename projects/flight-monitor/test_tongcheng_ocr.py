"""使用OCR识别同程页面上的航班号"""
import ddddocr
import time
from playwright.sync_api import sync_playwright


def ocr_tongcheng(dep_code, arr_code, date_str):
    """OCR识别同程航班号"""
    print(f"\n{'='*70}")
    print(f"[同程OCR识别] {dep_code} -> {arr_code}, {date_str}")
    print('='*70)
    
    # 初始化OCR
    ocr = ddddocr.DdddOcr()
    
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
            
            # 查找航班号元素并截图
            print("\n查找航班号元素...")
            
            # 尝试多种选择器
            selectors = [
                '.flight-number',
                '.flight-no',
                '[class*="flight"]',
                '.airline-info',
            ]
            
            for selector in selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        print(f"\n选择器 '{selector}' 找到 {len(elements)} 个元素")
                        
                        for i, elem in enumerate(elements[:3]):
                            # 截图
                            screenshot_path = f'/tmp/tongcheng_ocr_{i}.png'
                            elem.screenshot(path=screenshot_path)
                            print(f"  元素 {i+1} 截图已保存: {screenshot_path}")
                            
                            # OCR识别
                            with open(screenshot_path, 'rb') as f:
                                img_bytes = f.read()
                                result = ocr.classification(img_bytes)
                                print(f"  OCR结果: {result}")
                except Exception as e:
                    print(f"  选择器 '{selector}' 失败: {e}")
            
            # 如果没有找到特定元素，截图整个页面
            print("\n截图整个页面...")
            page.screenshot(path='/tmp/tongcheng_full.png')
            print("✓ 完整页面截图已保存")
            
            # 尝试识别页面中的航班号区域
            print("\n尝试识别页面中的航班号...")
            
            # 获取页面文本
            text = page.inner_text('body')
            
            # 查找可能的航班号位置
            import re
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if any(x in line for x in ['航班', 'flight', '航空']):
                    print(f"  行 {i}: {line[:100]}")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    ocr_tongcheng("CAN", "TAO", "2026-03-14")
