"""提取同程字体文件"""
import re
import requests
import time
from playwright.sync_api import sync_playwright


def extract_tongcheng_font(dep_code, arr_code, date_str):
    """提取字体文件"""
    print(f"\n{'='*70}")
    print(f"[同程字体提取] {dep_code} -> {arr_code}, {date_str}")
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
            
            # 查找字体文件URL
            print("\n查找字体文件...")
            
            # 字体文件模式
            font_patterns = [
                r'url\(["\']?([^"\']+\.woff[^"\']*)["\']?\)',
                r'url\(["\']?([^"\']+\.ttf[^"\']*)["\']?\)',
                r'src\s*:\s*url\(["\']?([^"\']+)["\']?\)',
            ]
            
            font_urls = []
            for pattern in font_patterns:
                matches = re.findall(pattern, html)
                font_urls.extend(matches)
            
            # 去重
            font_urls = list(set(font_urls))
            
            print(f"找到 {len(font_urls)} 个字体文件:")
            for url in font_urls[:5]:
                print(f"  {url}")
                
                # 尝试下载字体文件
                try:
                    if url.startswith('http'):
                        font_resp = requests.get(url, timeout=30)
                        if font_resp.status_code == 200:
                            font_path = f'/tmp/tongcheng_font_{url.split("/")[-1][:20]}'
                            with open(font_path, 'wb') as f:
                                f.write(font_resp.content)
                            print(f"    ✓ 字体文件已保存: {font_path}")
                except Exception as e:
                    print(f"    ✗ 下载失败: {e}")
            
            # 查找CSS中的font-family定义
            print("\n查找字体定义...")
            font_family_matches = re.findall(r'font-family\s*:\s*["\']?([^"\']+)["\']?', html)
            for ff in font_family_matches[:5]:
                print(f"  font-family: {ff}")
            
            browser.close()
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    extract_tongcheng_font("CAN", "TAO", "2026-03-14")
