"""同程字体解密 - 字形指纹法"""
from fontTools.ttLib import TTFont
import json
import os


def extract_glyph_fingerprint(font_path):
    """提取字形指纹"""
    print(f"\n{'='*70}")
    print(f"提取字形指纹: {os.path.basename(font_path)}")
    print('='*70)
    
    fingerprints = {}
    
    try:
        font = TTFont(font_path)
        glyf_table = font.get('glyf')
        
        if not glyf_table:
            print("✗ 无glyf表")
            return {}
        
        # 遍历所有字形
        for glyph_name in glyf_table.glyphOrder:
            glyph = glyf_table[glyph_name]
            
            # 提取轮廓信息
            if hasattr(glyph, 'program'):
                # 有指令的复杂字形
                fingerprint = extract_complex_glyph(glyph)
            else:
                # 简单字形
                fingerprint = extract_simple_glyph(glyph)
            
            if fingerprint:
                fingerprints[glyph_name] = fingerprint
        
        font.close()
        
        print(f"提取了 {len(fingerprints)} 个字形指纹")
        return fingerprints
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        return {}


def extract_simple_glyph(glyph):
    """提取简单字形指纹"""
    try:
        if hasattr(glyph, 'numberOfContours') and glyph.numberOfContours > 0:
            # 使用轮廓数量和边界框作为指纹
            return {
                'contours': glyph.numberOfContours,
                'bbox': [glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax],
                'type': 'simple'
            }
    except:
        pass
    return None


def extract_complex_glyph(glyph):
    """提取复杂字形指纹"""
    try:
        # 获取指令数量
        program = glyph.program
        if hasattr(program, 'bytecode'):
            bytecode_len = len(program.bytecode)
        else:
            bytecode_len = 0
        
        # 使用轮廓数量和指令长度作为指纹
        return {
            'contours': getattr(glyph, 'numberOfContours', 0),
            'bytecode_len': bytecode_len,
            'type': 'complex'
        }
    except:
        return None


def build_reference_mapping():
    """建立标准数字的参考指纹"""
    # 标准数字0-9的轮廓特征（近似值）
    reference = {
        '0': {'contours': 2, 'description': '两个轮廓（外圈+内圈）'},
        '1': {'contours': 1, 'description': '一个轮廓'},
        '2': {'contours': 1, 'description': '一个轮廓'},
        '3': {'contours': 1, 'description': '一个轮廓'},
        '4': {'contours': 1, 'description': '一个轮廓'},
        '5': {'contours': 1, 'description': '一个轮廓'},
        '6': {'contours': 1, 'description': '一个轮廓'},
        '7': {'contours': 1, 'description': '一个轮廓'},
        '8': {'contours': 2, 'description': '两个轮廓'},
        '9': {'contours': 1, 'description': '一个轮廓'},
    }
    return reference


def match_glyph_to_digit(fingerprint, reference):
    """匹配字形到数字"""
    contours = fingerprint.get('contours', 0)
    
    # 根据轮廓数量匹配
    if contours == 2:
        # 可能是0或8
        return ['0', '8']
    elif contours == 1:
        # 可能是1-7,9
        return ['1', '2', '3', '4', '5', '6', '7', '9']
    else:
        return ['?']


if __name__ == "__main__":
    # 分析字体文件
    font_path = '/tmp/tongcheng_font_TongChengCurrency-Re'
    
    if os.path.exists(font_path):
        fingerprints = extract_glyph_fingerprint(font_path)
        
        # 显示前20个字形
        print("\n前20个字形指纹:")
        for i, (name, fp) in enumerate(list(fingerprints.items())[:20]):
            print(f"  {name}: {fp}")
        
        # 保存指纹
        with open('/tmp/tongcheng_fingerprints.json', 'w') as f:
            json.dump(fingerprints, f, indent=2)
        print("\n✓ 指纹已保存到 /tmp/tongcheng_fingerprints.json")
        
        # 建立参考映射
        reference = build_reference_mapping()
        print("\n参考映射:")
        for digit, info in reference.items():
            print(f"  {digit}: {info['description']}")
    else:
        print(f"✗ 字体文件不存在: {font_path}")
