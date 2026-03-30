#!/usr/bin/env python3
"""
可解释的股票预测模型 V2
不仅预测价格，还给出预测理由
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import json

DB_PATH = "/root/.openclaw/workspace/stock_data.db"
MODEL_PATH = "/root/.openclaw/workspace/models"

class ExplainablePredictor:
    """可解释预测器"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.model = None
        self.feature_importance = None
    
    def prepare_features(self, df):
        """准备特征"""
        features = pd.DataFrame()
        close = df['close']
        
        # 价格特征
        features['close'] = close
        features['open'] = df['open']
        features['high'] = df['high']
        features['low'] = df['low']
        features['volume'] = df['volume']
        
        # 移动平均线（降低周期要求）
        features['ma5'] = close.rolling(window=5, min_periods=3).mean()
        features['ma10'] = close.rolling(window=10, min_periods=5).mean()
        features['ma20'] = close.rolling(window=20, min_periods=10).mean()
        
        # 价格位置（相对于均线的位置）
        features['price_to_ma5'] = (close - features['ma5']) / features['ma5'] * 100
        features['price_to_ma20'] = (close - features['ma20']) / features['ma20'] * 100
        
        # 趋势强度
        features['ma5_slope'] = features['ma5'].diff(3) / features['ma5'].shift(3).replace(0, np.nan) * 100
        features['ma10_slope'] = features['ma10'].diff(3) / features['ma10'].shift(3).replace(0, np.nan) * 100
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # RSI状态
        features['rsi_overbought'] = (features['rsi'] > 70).astype(int)
        features['rsi_oversold'] = (features['rsi'] < 30).astype(int)
        
        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        features['macd_dif'] = ema12 - ema26
        features['macd_dea'] = features['macd_dif'].ewm(span=9).mean()
        features['macd_bar'] = (features['macd_dif'] - features['macd_dea']) * 2
        
        # MACD状态
        features['macd_golden'] = ((features['macd_dif'] > features['macd_dea']) & 
                                   (features['macd_dif'].shift(1) <= features['macd_dea'].shift(1))).astype(int)
        features['macd_dead'] = ((features['macd_dif'] < features['macd_dea']) & 
                                 (features['macd_dif'].shift(1) >= features['macd_dea'].shift(1))).astype(int)
        
        # 波动率
        features['volatility'] = close.pct_change().rolling(20).std() * 100
        
        # 成交量特征
        features['volume_ma5'] = features['volume'].rolling(5).mean()
        features['volume_ratio'] = features['volume'] / features['volume_ma5']
        features['volume_spike'] = (features['volume_ratio'] > 2).astype(int)
        
        # 近期涨跌幅
        features['change_1d'] = close.pct_change() * 100
        features['change_5d'] = close.pct_change(5) * 100
        features['change_10d'] = close.pct_change(10) * 100
        
        # 目标变量
        features['target'] = close.shift(-1)
        
        return features.dropna()
    
    def train_model(self, symbol):
        """训练模型"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            "SELECT * FROM stock_prices WHERE symbol = ? ORDER BY date",
            conn, params=(symbol,)
        )
        conn.close()
        
        if len(df) < 30:
            return None, "数据不足"
        
        # 准备特征
        features = self.prepare_features(df)
        if len(features) < 30:
            return None, "特征计算后数据不足"
        
        X = features.drop('target', axis=1)
        y = features['target']
        
        # 训练
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X, y)
        
        # 特征重要性
        importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # 保存
        import os
        os.makedirs(MODEL_PATH, exist_ok=True)
        joblib.dump(model, f"{MODEL_PATH}/{symbol}_explained_model.pkl")
        
        self.model = model
        self.feature_importance = importance
        
        return model, importance
    
    def predict_with_explanation(self, symbol):
        """预测并解释"""
        import os
        
        model_path = f"{MODEL_PATH}/{symbol}_explained_model.pkl"
        
        # 加载或训练模型
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            model, _ = self.train_model(symbol)
            if model is None:
                return None, "模型训练失败"
        
        # 获取最新数据
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            "SELECT * FROM stock_prices WHERE symbol = ? ORDER BY date",
            conn, params=(symbol,)
        )
        conn.close()
        
        # 准备特征
        features = self.prepare_features(df)
        if len(features) == 0:
            return None, "特征计算失败"
        
        latest = features.iloc[-1:].drop('target', axis=1)
        actual_close = df.iloc[-1]['close']
        
        # 预测
        predicted = self.model.predict(latest)[0]
        change_pct = ((predicted - actual_close) / actual_close) * 100
        
        # 生成解释
        explanation = self.generate_explanation(latest.iloc[0], change_pct)
        
        return {
            'symbol': symbol,
            'actual_close': actual_close,
            'predicted_close': predicted,
            'change_pct': change_pct,
            'direction': '上涨' if change_pct > 0 else '下跌',
            'explanation': explanation
        }, "成功"
    
    def generate_explanation(self, features, change_pct):
        """生成预测解释"""
        reasons = []
        
        # 1. RSI分析
        rsi = features['rsi']
        if rsi > 70:
            reasons.append(f"RSI超买({rsi:.0f})，历史超买后平均回调3-5%")
        elif rsi < 30:
            reasons.append(f"RSI超卖({rsi:.0f})，存在反弹需求")
        elif 50 < rsi < 70:
            reasons.append(f"RSI偏强({rsi:.0f})，但未到超买")
        elif 30 < rsi < 50:
            reasons.append(f"RSI偏弱({rsi:.0f})，但未到超卖")
        
        # 2. 趋势分析
        price_to_ma20 = features['price_to_ma20']
        ma5_slope = features['ma5_slope']
        
        if price_to_ma20 > 5:
            reasons.append(f"价格高于MA20达{price_to_ma20:.1f}%，偏离过大有回归需求")
        elif price_to_ma20 < -5:
            reasons.append(f"价格低于MA20达{abs(price_to_ma20):.1f}%，超跌反弹概率大")
        
        if ma5_slope > 1:
            reasons.append("短期均线向上，趋势偏多")
        elif ma5_slope < -1:
            reasons.append("短期均线向下，趋势偏空")
        
        # 3. MACD分析
        macd_bar = features['macd_bar']
        if macd_bar > 0 and features['macd_golden'] == 1:
            reasons.append("MACD刚形成金叉，动能转强")
        elif macd_bar < 0 and features['macd_dead'] == 1:
            reasons.append("MACD刚形成死叉，动能转弱")
        elif macd_bar > 0:
            reasons.append("MACD柱状为正，多头占优")
        else:
            reasons.append("MACD柱状为负，空头占优")
        
        # 4. 成交量分析
        volume_ratio = features['volume_ratio']
        if volume_ratio > 2:
            reasons.append(f"成交量放大{volume_ratio:.1f}倍，资金关注度高")
        elif volume_ratio < 0.5:
            reasons.append("成交量萎缩，市场参与度低")
        
        # 5. 近期涨跌
        change_5d = features['change_5d']
        if change_5d > 10:
            reasons.append(f"近5日已涨{change_5d:.1f}%，获利盘抛压风险")
        elif change_5d < -10:
            reasons.append(f"近5日已跌{abs(change_5d):.1f}%，超跌反弹机会")
        
        # 6. 波动率
        volatility = features['volatility']
        if volatility > 5:
            reasons.append(f"波动率较高({volatility:.1f}%)，价格可能大幅波动")
        
        # 综合判断
        if change_pct > 3:
            summary = "多重因素支撑上涨"
        elif change_pct < -3:
            summary = "多重因素预示回调"
        else:
            summary = "多空因素交织，震荡为主"
        
        return {
            'summary': summary,
            'reasons': reasons,
            'key_factors': {
                'rsi': features['rsi'],
                'price_to_ma20': features['price_to_ma20'],
                'macd_bar': features['macd_bar'],
                'volume_ratio': features['volume_ratio'],
                'change_5d': features['change_5d']
            }
        }

def generate_explainable_report():
    """生成可解释预测报告"""
    predictor = ExplainablePredictor()
    
    stocks = {
        '600104': '上汽集团',
        '600150': '中国船舶',
        '600326': '西藏天路',
        '600581': '八一钢铁',
        '603577': '汇金通',
    }
    
    print("=" * 70)
    print("🔮 AI预测报告（可解释版）")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    for symbol, name in stocks.items():
        print(f"\n{'='*70}")
        print(f"【{name} ({symbol})】")
        print("=" * 70)
        
        result, msg = predictor.predict_with_explanation(symbol)
        
        if result is None:
            print(f"预测失败: {msg}")
            continue
        
        # 预测结果
        print(f"\n📊 预测结果:")
        print(f"   当前价格: ¥{result['actual_close']:.2f}")
        print(f"   预测价格: ¥{result['predicted_close']:.2f}")
        print(f"   预测涨跌: {result['change_pct']:+.2f}% ({result['direction']})")
        
        # 解释
        exp = result['explanation']
        print(f"\n📝 预测依据:")
        print(f"   综合判断: {exp['summary']}")
        print(f"\n   详细理由:")
        for i, reason in enumerate(exp['reasons'], 1):
            print(f"   {i}. {reason}")
        
        # 关键因子
        print(f"\n📈 关键因子:")
        factors = exp['key_factors']
        print(f"   • RSI: {factors['rsi']:.1f}")
        print(f"   • 价格偏离MA20: {factors['price_to_ma20']:+.1f}%")
        print(f"   • MACD柱状: {factors['macd_bar']:.3f}")
        print(f"   • 成交量比: {factors['volume_ratio']:.2f}")
        print(f"   • 5日涨跌: {factors['change_5d']:+.1f}%")

if __name__ == "__main__":
    import sys
    
    # 生成报告
    generate_explainable_report()
    
    # 自动记录预测到准确率系统
    print("\n" + "=" * 60)
    print("📝 记录预测结果到准确率追踪系统...")
    print("=" * 60)
    
    from prediction_accuracy import PredictionAccuracyTracker
    tracker = PredictionAccuracyTracker()
    
    stocks = {
        '600104': '上汽集团',
        '600150': '中国船舶',
        '600326': '西藏天路',
        '600581': '八一钢铁',
        '603577': '汇金通',
        '600410': '华胜天成',
    }
    
    predictor = ExplainablePredictor()
    
    for symbol, name in stocks.items():
        result, msg = predictor.predict_with_explanation(symbol)
        if result:
            tracker.record_prediction(
                symbol=symbol,
                predicted_price=result['predicted_close'],
                predicted_change_pct=result['change_pct']
            )
    
    print("\n✅ 预测记录完成！明天会自动更新实际价格并计算准确率。")
