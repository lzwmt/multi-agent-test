#!/usr/bin/env python3
"""
股票分析系统 V2 - 通用专业版
基于行业标准参数配置
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/stock_data.db"

# 股票列表
STOCKS = {
    '600104': '上汽集团',
    '600150': '中国船舶',
    '600326': '西藏天路',
    '600581': '八一钢铁',
    '603577': '汇金通',
}

class StockAnalyzerV2:
    """专业股票分析器"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def calculate_ma(self, series, window):
        """计算移动平均线"""
        return series.rolling(window=window).mean()
    
    def calculate_rsi(self, series, window=14):
        """计算RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self, series, fast=12, slow=26, signal=9):
        """计算MACD (12,26,9标准参数)"""
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal).mean()
        bar = (dif - dea) * 2
        return dif, dea, bar
    
    def calculate_bollinger(self, series, window=20, num_std=2):
        """计算布林带 (20日,2倍标准差)"""
        mid = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        upper = mid + (std * num_std)
        lower = mid - (std * num_std)
        return upper, mid, lower
    
    def analyze_technical(self, df):
        """技术分析 - 专业版"""
        close = df['close']
        
        # 计算指标
        ma5 = self.calculate_ma(close, 5)
        ma10 = self.calculate_ma(close, 10)
        ma20 = self.calculate_ma(close, 20)
        ma60 = self.calculate_ma(close, 60)
        
        rsi6 = self.calculate_rsi(close, 6)
        rsi12 = self.calculate_rsi(close, 12)
        rsi24 = self.calculate_rsi(close, 24)
        
        macd_dif, macd_dea, macd_bar = self.calculate_macd(close)
        
        boll_upper, boll_mid, boll_lower = self.calculate_bollinger(close)
        
        # 最新值
        latest = {
            'close': close.iloc[-1],
            'ma5': ma5.iloc[-1],
            'ma10': ma10.iloc[-1],
            'ma20': ma20.iloc[-1],
            'ma60': ma60.iloc[-1],
            'rsi6': rsi6.iloc[-1],
            'rsi12': rsi12.iloc[-1],
            'rsi24': rsi24.iloc[-1],
            'macd_dif': macd_dif.iloc[-1],
            'macd_dea': macd_dea.iloc[-1],
            'macd_bar': macd_bar.iloc[-1],
            'boll_upper': boll_upper.iloc[-1],
            'boll_mid': boll_mid.iloc[-1],
            'boll_lower': boll_lower.iloc[-1],
        }
        
        return latest
    
    def generate_signals_v2(self, indicators):
        """生成交易信号 - 专业版"""
        signals = []
        score = 0
        
        close = indicators['close']
        ma5 = indicators['ma5']
        ma10 = indicators['ma10']
        ma20 = indicators['ma20']
        rsi6 = indicators['rsi6']
        rsi12 = indicators['rsi12']
        macd_bar = indicators['macd_bar']
        boll_upper = indicators['boll_upper']
        boll_lower = indicators['boll_lower']
        
        # ========== 1. 趋势判断 (40分) ==========
        if close > ma20 and ma5 > ma10:
            score += 40
            signals.append({
                'type': '趋势',
                'signal': '多头',
                'desc': '价格在MA20上方，MA5>MA10，趋势向上',
                'strength': '强'
            })
        elif close < ma20 and ma5 < ma10:
            score += 10
            signals.append({
                'type': '趋势',
                'signal': '空头',
                'desc': '价格在MA20下方，MA5<MA10，趋势向下',
                'strength': '弱'
            })
        else:
            score += 25
            signals.append({
                'type': '趋势',
                'signal': '震荡',
                'desc': '均线纠缠，趋势不明',
                'strength': '中'
            })
        
        # ========== 2. RSI判断 (30分) ==========
        avg_rsi = (rsi6 + rsi12) / 2
        
        if rsi6 < 20 and rsi12 < 25:
            score += 30
            signals.append({
                'type': 'RSI',
                'signal': '强烈超卖',
                'desc': f'RSI6={rsi6:.0f}, RSI12={rsi12:.0f}，严重超卖，反弹概率高',
                'strength': '强'
            })
        elif rsi6 < 30 or rsi12 < 30:
            score += 25
            signals.append({
                'type': 'RSI',
                'signal': '超卖',
                'desc': f'RSI6={rsi6:.0f}, RSI12={rsi12:.0f}，超卖区域，关注反弹',
                'strength': '中'
            })
        elif rsi6 > 80 and rsi12 > 75:
            score += 10
            signals.append({
                'type': 'RSI',
                'signal': '强烈超买',
                'desc': f'RSI6={rsi6:.0f}, RSI12={rsi12:.0f}，严重超买，回调风险高',
                'strength': '弱'
            })
        elif rsi6 > 70 or rsi12 > 70:
            score += 15
            signals.append({
                'type': 'RSI',
                'signal': '超买',
                'desc': f'RSI6={rsi6:.0f}, RSI12={rsi12:.0f}，超买区域，谨慎追高',
                'strength': '中'
            })
        else:
            score += 20
            signals.append({
                'type': 'RSI',
                'signal': '正常',
                'desc': f'RSI6={rsi6:.0f}, RSI12={rsi12:.0f}，正常区间',
                'strength': '中'
            })
        
        # ========== 3. MACD判断 (30分) ==========
        if macd_bar > 0 and macd_bar > indicators.get('macd_bar_prev', 0):
            score += 30
            signals.append({
                'type': 'MACD',
                'signal': '强势多头',
                'desc': 'MACD柱状为正且扩大，上涨动能增强',
                'strength': '强'
            })
        elif macd_bar > 0:
            score += 25
            signals.append({
                'type': 'MACD',
                'signal': '多头',
                'desc': 'MACD柱状为正，上涨动能',
                'strength': '中'
            })
        elif macd_bar < 0 and macd_bar < indicators.get('macd_bar_prev', 0):
            score += 10
            signals.append({
                'type': 'MACD',
                'signal': '强势空头',
                'desc': 'MACD柱状为负且扩大，下跌动能增强',
                'strength': '弱'
            })
        else:
            score += 15
            signals.append({
                'type': 'MACD',
                'signal': '空头',
                'desc': 'MACD柱状为负，下跌动能',
                'strength': '中'
            })
        
        # ========== 4. 布林带判断 (额外信号) ==========
        if close > boll_upper:
            signals.append({
                'type': '布林带',
                'signal': '突破上轨',
                'desc': '价格突破布林带上轨，超买状态',
                'strength': '中'
            })
        elif close < boll_lower:
            signals.append({
                'type': '布林带',
                'signal': '跌破下轨',
                'desc': '价格跌破布林带下轨，超卖状态',
                'strength': '中'
            })
        
        return score, signals
    
    def check_ai_conflict(self, tech_score, ai_prediction):
        """检测AI预测矛盾"""
        if ai_prediction is None:
            return None, "无AI预测"
        
        # 技术信号
        if tech_score >= 70:
            tech_signal = "买入"
        elif tech_score <= 30:
            tech_signal = "卖出"
        else:
            tech_signal = "观望"
        
        # AI信号
        ai_signal = "上涨" if ai_prediction > 0 else "下跌"
        ai_strength = abs(ai_prediction)
        
        # 检测矛盾
        if tech_signal == "买入" and ai_signal == "下跌":
            if ai_strength > 3:
                return "🔴 强烈矛盾", f"技术强烈买入但AI看跌{ai_prediction:.1f}%，建议观望"
            else:
                return "🟡 轻微矛盾", f"技术买入但AI小幅看跌{ai_prediction:.1f}%，谨慎操作"
        elif tech_signal == "卖出" and ai_signal == "上涨":
            if ai_strength > 3:
                return "🟢 强烈矛盾", f"技术强烈卖出但AI看涨{ai_prediction:.1f}%，可能反弹"
            else:
                return "🟡 轻微矛盾", f"技术卖出但AI小幅看涨{ai_prediction:.1f}%，观察"
        elif tech_signal == "观望" and abs(ai_prediction) > 2:
            return "💡 AI提示", f"技术观望但AI强烈{ai_signal}{ai_prediction:.1f}%，可关注"
        else:
            return "✅ 一致", f"技术和AI同向（技术{tech_signal}，AI{ai_signal}{ai_prediction:+.1f}%）"
    
    def get_recommendation(self, score, ai_prediction=None):
        """根据评分和AI预测给出建议"""
        # 基础建议
        if score >= 85:
            base_rec = "强烈买入"
            emoji = "🟢"
        elif score >= 70:
            base_rec = "买入"
            emoji = "🟢"
        elif score >= 55:
            base_rec = "谨慎买入"
            emoji = "🟡"
        elif score >= 45:
            base_rec = "持有观望"
            emoji = "🟡"
        elif score >= 30:
            base_rec = "谨慎持有"
            emoji = "🟠"
        elif score >= 15:
            base_rec = "减仓"
            emoji = "🔴"
        else:
            base_rec = "卖出"
            emoji = "🔴"
        
        # 矛盾检测
        conflict_flag, conflict_msg = self.check_ai_conflict(score, ai_prediction)
        
        # 调整建议
        if conflict_flag and "强烈矛盾" in conflict_flag:
            final_rec = "观望"
            emoji = "⚠️"
        elif conflict_flag and "轻微矛盾" in conflict_flag:
            final_rec = f"{base_rec}(注意矛盾)"
        else:
            final_rec = base_rec
        
        return final_rec, emoji, conflict_flag, conflict_msg
    
    def get_ai_prediction(self, symbol):
        """获取AI预测"""
        conn = sqlite3.connect(self.db_path)
        pred_df = pd.read_sql_query(
            "SELECT predicted_close, actual_close FROM price_predictions WHERE symbol = ? ORDER BY created_at DESC LIMIT 1",
            conn, params=(symbol,)
        )
        conn.close()
        
        if pred_df.empty:
            return None
        
        pred_close = pred_df.iloc[0]['predicted_close']
        actual_close = pred_df.iloc[0]['actual_close']
        change_pct = ((pred_close - actual_close) / actual_close) * 100
        return change_pct
    
    def analyze_stock(self, symbol):
        """分析单只股票"""
        conn = sqlite3.connect(self.db_path)
        
        # 获取数据
        df = pd.read_sql_query(
            "SELECT * FROM stock_prices WHERE symbol = ? ORDER BY date",
            conn, params=(symbol,)
        )
        
        if len(df) < 30:
            conn.close()
            return None
        
        # 技术分析
        indicators = self.analyze_technical(df)
        
        # 生成信号
        score, signals = self.generate_signals_v2(indicators)
        
        # 获取AI预测
        ai_prediction = self.get_ai_prediction(symbol)
        
        # 获取建议（含矛盾检测）
        recommendation, emoji, conflict_flag, conflict_msg = self.get_recommendation(score, ai_prediction)
        
        conn.close()
        
        return {
            'symbol': symbol,
            'name': STOCKS.get(symbol, symbol),
            'score': score,
            'recommendation': recommendation,
            'emoji': emoji,
            'indicators': indicators,
            'signals': signals,
            'ai_prediction': ai_prediction,
            'conflict_flag': conflict_flag,
            'conflict_msg': conflict_msg
        }
    
    def generate_report(self):
        """生成分析报告"""
        print("=" * 70)
        print("📊 股票技术分析报告 V2")
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
        
        results = []
        for symbol in STOCKS.keys():
            result = self.analyze_stock(symbol)
            if result:
                results.append(result)
                
                print(f"\n{result['emoji']} 【{result['name']} ({symbol})】")
                print(f"   综合评分: {result['score']}/100")
                print(f"   操作建议: 【{result['recommendation']}】")
                print(f"   当前价格: ¥{result['indicators']['close']:.2f}")
                
                # AI预测
                if result['ai_prediction'] is not None:
                    pred_emoji = "📈" if result['ai_prediction'] > 0 else "📉"
                    print(f"   AI预测: {pred_emoji} 明日 {result['ai_prediction']:+.1f}%")
                
                # 矛盾提示
                if result['conflict_flag']:
                    print(f"   {result['conflict_flag']}: {result['conflict_msg']}")
                
                print("\n   技术指标:")
                print(f"   • MA5: {result['indicators']['ma5']:.2f} | "
                      f"MA10: {result['indicators']['ma10']:.2f} | "
                      f"MA20: {result['indicators']['ma20']:.2f}")
                print(f"   • RSI6: {result['indicators']['rsi6']:.0f} | "
                      f"RSI12: {result['indicators']['rsi12']:.0f}")
                print(f"   • MACD: {result['indicators']['macd_bar']:.3f}")
                
                print("\n   信号分析:")
                for sig in result['signals']:
                    strength_emoji = "🔥" if sig['strength'] == '强' else "⚡" if sig['strength'] == '中' else "📍"
                    print(f"   {strength_emoji} [{sig['type']}] {sig['signal']}: {sig['desc']}")
        
        # 排序输出
        print("\n" + "=" * 70)
        print("📈 综合排名")
        print("=" * 70)
        results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)
        for i, r in enumerate(results_sorted, 1):
            print(f"{i}. {r['emoji']} {r['name']} ({r['symbol']}) - "
                  f"评分: {r['score']} - {r['recommendation']}")
        
        return results

if __name__ == "__main__":
    analyzer = StockAnalyzerV2()
    analyzer.generate_report()
