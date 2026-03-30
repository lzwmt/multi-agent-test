#!/usr/bin/env python3
"""
股票收盘报告 V2 - 整合 TrendRadar 行业新闻 + AI 预测分析
每天 15:30 发送
"""
import sys
import json
import sqlite3
import pickle
import os
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace')
from realtime_data import RealtimeDataSource

# Discord 频道
DISCORD_CHANNEL = "1480762206458085376"

# 股票及行业分类
STOCKS = {
    '600104': {'name': '上汽集团', 'industry': '汽车', 'industry_key': '新能源汽车产业链'},
    '600150': {'name': '中国船舶', 'industry': '船舶制造', 'industry_key': '船舶与海洋工程'},
    '600326': {'name': '西藏天路', 'industry': '基建', 'industry_key': '基建与建材'},
    '600581': {'name': '八一钢铁', 'industry': '钢铁', 'industry_key': '钢铁与冶金'},
    '603577': {'name': '汇金通', 'industry': '电力设备', 'industry_key': '电力与新能源'},
    '600410': {'name': '华胜天成', 'industry': '科技', 'industry_key': '科技与数字化'},
}

# TrendRadar 数据库路径
TRENDRADAR_DB_PATH = '/root/.openclaw/workspace/TrendRadar/output/news'

def get_stock_data():
    """获取股票今日数据"""
    data = {}
    for symbol, info in STOCKS.items():
        try:
            result, msg = RealtimeDataSource.tencent_realtime(symbol)
            if result:
                data[symbol] = {
                    'name': info['name'],
                    'industry': info['industry'],
                    'industry_key': info['industry_key'],
                    'price': result['price'],
                    'change_pct': result['change_pct'],
                    'change_amount': result['change_amount'],
                    'open': result['open'],
                    'high': result['high'],
                    'low': result['low'],
                    'yesterday_close': result['yesterday_close'],
                    'volume': result['volume'],
                    'turnover': result['turnover'],
                }
        except Exception as e:
            print(f"获取 {symbol} 失败: {e}")
    return data

def get_industry_news_from_trendradar():
    """从 TrendRadar 数据库获取今日行业热点新闻"""
    news_by_industry = {}
    today = datetime.now().strftime('%Y-%m-%d')
    db_path = os.path.join(TRENDRADAR_DB_PATH, f'{today}.db')
    
    if not os.path.exists(db_path):
        return news_by_industry
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 行业关键词映射
        industry_keywords = {
            '新能源汽车产业链': ['新能源汽车', '电动车', '电动汽车', '混动', '插混', '纯电', '锂电池', '动力电池', '宁德时代', '充电桩', '换电站', '汽车销量', '乘用车', '新能源车销量', '汽车出口', '汽车下乡', '智能驾驶', '自动驾驶', '智能座舱', '车联网', '整车厂商', '比亚迪', '蔚来', '小鹏', '理想', '特斯拉'],
            '船舶与海洋工程': ['船舶', '造船', '船厂', '船东', '新船订单', '船舶出口', '邮轮', 'LNG船', '集装箱船', '散货船', '油轮', '航母', '军舰', '舰艇', '驱逐舰', '护卫舰', '潜艇', '海军装备', '海工装备', '海洋工程', '深海装备', '海上风电安装', '钻井平台', '航运', '海运', '港口', '集装箱运价'],
            '基建与建材': ['水泥', '建材', '玻璃', '陶瓷', '防水材料', '涂料', '基建投资', '固定资产投资', '新基建', '传统基建', '西部大开发', '西部建设', '成渝经济圈', '房地产', '楼市', '房价', '房企', '拿地', '开工', '一带一路', '海外基建', '西藏', '拉萨', '林芝', '川藏铁路'],
            '钢铁与冶金': ['钢铁', '钢材', '螺纹钢', '线材', '热轧', '冷轧', '铁矿石', '焦炭', '焦煤', '废钢', '合金', '钢铁产能', '粗钢产量', '钢铁价格', '钢材市场', '供给侧改革', '去产能', '环保限产', '钢铁整合', '新疆', '乌鲁木齐', '兵团', '中亚', '丝绸之路经济带'],
            '电力与新能源': ['特高压', '超高压', '输电', '变电站', '电网投资', '智能电网', '国家电网', '南方电网', '西电东送', '电力改革', '储能', '储能电池', '储能系统', '抽水蓄能', '光伏', '光伏发电', '光伏电站', '光伏组件', '硅料', '风电', '风力发电', '海上风电', '风机', '核电', '核电机组', '新能源发电', '可再生能源', '清洁能源', '碳中和'],
            '科技与数字化': ['云计算', '云服务', '云原生', '私有云', '公有云', '混合云', '边缘计算', 'IT服务', '系统集成', '企业数字化', '数字化转型', '信息化', '大数据', '数据中台', '数据治理', '数据分析', '数据要素', '人工智能应用', 'AI应用', '行业AI', 'AI解决方案', '信创', '国产软件', '国产操作系统', '国产数据库', '工业互联网', '智能制造', '工业软件', '东数西算', '数据中心', '算力', '智算中心']
        }
        
        cursor.execute('SELECT title, platform_id, rank FROM news_items')
        rows = cursor.fetchall()
        
        for title, platform, rank in rows:
            for industry, kws in industry_keywords.items():
                for kw in kws:
                    if kw in title:
                        if industry not in news_by_industry:
                            news_by_industry[industry] = []
                        # 去重
                        if not any(n['title'] == title for n in news_by_industry[industry]):
                            news_by_industry[industry].append({
                                'title': title,
                                'platform': platform,
                                'rank': rank,
                                'keyword': kw
                            })
                        break
        
        conn.close()
    except Exception as e:
        print(f"读取 TrendRadar 数据失败: {e}")
    
    return news_by_industry

def get_ai_prediction(symbol):
    """获取 AI 预测结果 - 使用 stock_predictor_v2 的模型"""
    try:
        import sys
        sys.path.insert(0, '/root/.openclaw/workspace')
        from stock_predictor_v2 import ExplainablePredictor
        
        predictor = ExplainablePredictor()
        result, msg = predictor.predict_with_explanation(symbol)
        
        if result:
            return {
                'trend': result['direction'],
                'change_pct': result['change_pct'],
                'predicted_price': result['predicted_close'],
                'confidence': min(abs(result['change_pct']) / 5, 0.9),  # 根据预测幅度估算置信度
                'reason': result['explanation']['summary'],
                'detail_reasons': result['explanation']['reasons'][:3]  # 取前3个详细理由
            }
    except Exception as e:
        print(f"获取 {symbol} AI预测失败: {e}")
    
    return None

def format_report(stock_data, industry_news):
    """格式化收盘报告"""
    date_str = datetime.now().strftime("%Y年%m月%d日")
    
    lines = [
        f"📊 **股票收盘报告** - {date_str}",
        "",
        "🏆 **今日个股表现**",
        "",
    ]
    
    # 按涨跌幅排序
    sorted_stocks = sorted(stock_data.items(), key=lambda x: x[1]['change_pct'], reverse=True)
    
    for symbol, data in sorted_stocks:
        emoji = "🟢" if data['change_pct'] >= 0 else "🔴"
        lines.append(f"{emoji} **{data['name']}** ({symbol})")
        lines.append(f"   收盘价: ¥{data['price']:.2f}")
        lines.append(f"   涨跌: {data['change_pct']:+.2f}% ({data['change_amount']:+.2f})")
        lines.append(f"   最高: ¥{data['high']:.2f} | 最低: ¥{data['low']:.2f}")
        # 格式化成交量和成交额
        # 成交量：API返回的是手，转换为万股
        volume_wan = data['volume'] / 10000
        # 成交额：腾讯API返回的是万元，转换为亿
        turnover_yi = data['turnover'] / 10000
        lines.append(f"   成交量: {volume_wan:.1f}万手")
        lines.append(f"   成交额: ¥{turnover_yi:.2f}亿")
        
        # AI 预测
        prediction = get_ai_prediction(symbol)
        if prediction:
            trend_emoji = "📈" if prediction['trend'] == '上涨' else "📉" if prediction['trend'] == '下跌' else "➡️"
            lines.append(f"   {trend_emoji} AI预测: {prediction['trend']} {prediction['change_pct']:+.2f}%")
            lines.append(f"      目标价: ¥{prediction['predicted_price']:.2f} | 置信度: {prediction['confidence']*100:.0f}%")
            lines.append(f"      理由: {prediction['reason']}")
            if prediction.get('detail_reasons'):
                for reason in prediction['detail_reasons']:
                    lines.append(f"      • {reason}")
        
        lines.append("")
    
    # 行业热点新闻
    lines.append("📰 **今日行业热点**")
    lines.append("")
    
    for symbol, data in sorted_stocks:
        industry_key = data['industry_key']
        if industry_key in industry_news and industry_news[industry_key]:
            lines.append(f"【{data['name']} - {data['industry']}】")
            for i, news in enumerate(industry_news[industry_key][:3], 1):  # 每个行业最多3条
                lines.append(f"   {i}. {news['title']}")
                lines.append(f"      来源: {news['platform']} | 热度排名: {news['rank']}")
            lines.append("")
    
    # 总结
    total_up = sum(1 for d in stock_data.values() if d['change_pct'] >= 0)
    total_down = len(stock_data) - total_up
    
    lines.append("📈 **今日总结**")
    lines.append(f"   上涨: {total_up}只 | 下跌: {total_down}只")
    if sorted_stocks:
        lines.append(f"   最强: {sorted_stocks[0][1]['name']} (+{sorted_stocks[0][1]['change_pct']:.2f}%)")
        lines.append(f"   最弱: {sorted_stocks[-1][1]['name']} ({sorted_stocks[-1][1]['change_pct']:.2f}%)")
    lines.append("")
    lines.append("⏰ 数据时间: 收盘后")
    lines.append("💡 明日开盘: 9:30")
    lines.append("📊 行业数据来源: TrendRadar")
    
    return "\n".join(lines)

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 生成收盘报告 V2...")
    
    # 获取股票数据
    stock_data = get_stock_data()
    if not stock_data:
        print("获取股票数据失败")
        return 1
    
    # 获取行业新闻
    print("正在获取 TrendRadar 行业新闻...")
    industry_news = get_industry_news_from_trendradar()
    print(f"获取到 {len(industry_news)} 个行业的 {sum(len(v) for v in industry_news.values())} 条新闻")
    
    # 生成报告
    report = format_report(stock_data, industry_news)
    
    # 发送 Discord 消息
    print("\n" + "="*50)
    print("正在发送 Discord 消息...")
    
    try:
        import requests
        # 获取 Discord webhook URL
        webhook_url = "https://discord.com/api/webhooks/..."  # 需要在环境变量或配置中设置
        
        # 使用 OpenClaw 的消息发送机制
        # 这里通过调用 message 工具发送
        print("DISCORD_MESSAGE_START")
        print(json.dumps({
            "channel": "discord",
            "to": DISCORD_CHANNEL,
            "message": report
        }, ensure_ascii=False))
        print("DISCORD_MESSAGE_END")
        print("="*50)
        print("报告生成完成，请通过 OpenClaw 消息工具发送")
    except Exception as e:
        print(f"发送失败: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
