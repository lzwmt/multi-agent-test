"""分析同程字体文件"""
from fontTools.ttLib import TTFont
import os


def analyze_font(font_path):
    """分析字体文件"""
    print(f"\n{'='*70}")
    print(f"分析字体: {os.path.basename(font_path)}")
    print('='*70)
    
    try:
        font = TTFont(font_path)
        
        # 获取字符映射
        cmap = font.getBestCmap()
        print(f"\n字符映射表 (cmap) 条目数: {len(cmap) if cmap else 0}")
        
        if cmap:
            print("\n前20个字符映射:")
            for i, (unicode_val, glyph_name) in enumerate(list(cmap.items())[:20]):
                char = chr(unicode_val)
                print(f"  U+{unicode_val:04X} ({char!r}) -> {glyph_name}")
        
        # 获取字形信息
        glyf_table = font.get('glyf')
        if glyf_table:
            print(f"\n字形表 (glyf) 条目数: {len(glyf_table.glyphOrder)}")
            
            # 分析前几个字形
            print("\n前10个字形信息:")
            for glyph_name in glyf_table.glyphOrder[:10]:
                glyph = glyf_table[glyph_name]
                if hasattr(glyph, 'program'):
                    print(f"  {glyph_name}: 有程序指令")
                else:
                    print(f"  {glyph_name}: 简单字形")
        
        # 获取字体名称
        name_table = font.get('name')
        if name_table:
            print("\n字体名称:")
            for record in name_table.names[:5]:
                try:
                    print(f"  {record.nameID}: {record.toStr()}")
                except:
                    pass
        
        font.close()
        
    except Exception as e:
        print(f"✗ 错误: {e}")


if __name__ == "__main__":
    # 分析所有字体文件
    font_files = [
        '/tmp/tongcheng_font_iconfont.ttf?t=16793',
        '/tmp/tongcheng_font_iconfont.ttf?t=17610',
        '/tmp/tongcheng_font_iconfont.woff?t=1679',
        '/tmp/tongcheng_font_TongChengCurrency-Re',
    ]
    
    for font_path in font_files:
        if os.path.exists(font_path):
            analyze_font(font_path)
        else:
            print(f"\n✗ 文件不存在: {font_path}")
