#!/usr/bin/env python3
"""
股票价格预测模型
使用机器学习预测未来价格走势
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib
import json

DB_PATH = "/root/.openclaw/workspace/stock_data.db"
MODEL_PATH = "/root/.openclaw/workspace/models"

def init_prediction_tables():
    """初始化预测表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 预测结果表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            date TEXT,
            actual_close REAL,
            predicted_close REAL,
            prediction_date TEXT,
            model_version TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 趋势预测表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trend_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            date TEXT,
            actual_trend TEXT,
            predicted_trend TEXT,
            up_probability REAL,
            down_probability REAL,
            prediction_date TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("预测表初始化完成")

def prepare_features(df):
    """准备特征数据"""
    features = pd.DataFrame()
    
    # 价格特征
    features['close'] = df['close']
    features['open'] = df['open']
    features['high'] = df['high']
    features['low'] = df['low']
    features['volume'] = df['volume']
    
    # 技术指标
    features['ma5'] = df['close'].rolling(window=5).mean()
    features['ma10'] = df['close'].rolling(window=10).mean()
    features['ma20'] = df['close'].rolling(window=20).mean()
    
    # 价格变化
    features['price_change'] = df['close'].pct_change()
    features['price_change_5d'] = df['close'].pct_change(periods=5)
    
    # 波动率
    features['volatility'] = df['close'].rolling(window=20).std()
    
    # 成交量特征
    features['volume_ma5'] = df['volume'].rolling(window=5).mean()
    features['volume_ratio'] = df['volume'] / features['volume_ma5']
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    features['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    features['macd'] = ema12 - ema26
    features['macd_signal'] = features['macd'].ewm(span=9).mean()
    
    # 目标变量：次日收盘价
    features['target_price'] = df['close'].shift(-1)
    
    # 目标变量：趋势（1=上涨, 0=下跌/平）
    features['target_trend'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    return features.dropna()

def train_price_model(symbol, df):
    """训练价格预测模型"""
    features = prepare_features(df)
    if len(features) < 30:
        print(f"{symbol}: 数据不足，无法训练")
        return None
    
    X = features.drop(['target_price', 'target_trend'], axis=1)
    y_price = features['target_price']
    
    # 划分训练测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_price, test_size=0.2, shuffle=False
    )
    
    # 训练模型
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # 评估
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    
    print(f"  价格模型 RMSE: {rmse:.4f}")
    
    # 保存模型
    import os
    os.makedirs(MODEL_PATH, exist_ok=True)
    joblib.dump(model, f"{MODEL_PATH}/{symbol}_price_model.pkl")
    
    # 保存特征重要性
    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    return model, importance

def train_trend_model(symbol, df):
    """训练趋势预测模型"""
    features = prepare_features(df)
    if len(features) < 30:
        return None
    
    X = features.drop(['target_price', 'target_trend'], axis=1)
    y_trend = features['target_trend']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_trend, test_size=0.2, shuffle=False
    )
    
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"  趋势模型准确率: {accuracy:.2%}")
    
    joblib.dump(model, f"{MODEL_PATH}/{symbol}_trend_model.pkl")
    
    return model, accuracy

def predict_next_day(symbol, df):
    """预测下一个交易日"""
    import os
    
    price_model_path = f"{MODEL_PATH}/{symbol}_price_model.pkl"
    trend_model_path = f"{MODEL_PATH}/{symbol}_trend_model.pkl"
    
    if not os.path.exists(price_model_path) or not os.path.exists(trend_model_path):
        print(f"{symbol}: 模型不存在，请先训练")
        return None
    
    # 加载模型
    price_model = joblib.load(price_model_path)
    trend_model = joblib.load(trend_model_path)
    
    # 准备最新特征
    features = prepare_features(df)
    if len(features) == 0:
        return None
    
    latest = features.iloc[-1:].drop(['target_price', 'target_trend'], axis=1)
    
    # 预测
    price_pred = price_model.predict(latest)[0]
    trend_pred = trend_model.predict(latest)[0]
    trend_proba = trend_model.predict_proba(latest)[0]
    
    actual_close = features.iloc[-1]['close']
    predicted_change = ((price_pred - actual_close) / actual_close) * 100
    
    return {
        'symbol': symbol,
        'date': df.iloc[-1]['date'],
        'actual_close': actual_close,
        'predicted_close': price_pred,
        'predicted_change_pct': predicted_change,
        'predicted_trend': '上涨' if trend_pred == 1 else '下跌',
        'up_probability': trend_proba[1],
        'down_probability': trend_proba[0],
        'confidence': max(trend_proba)
    }

def train_all_models():
    """训练所有股票的模型"""
    conn = sqlite3.connect(DB_PATH)
    symbols = pd.read_sql_query(
        "SELECT DISTINCT symbol FROM stock_prices", conn
    )['symbol'].tolist()
    conn.close()
    
    print(f"开始训练 {len(symbols)} 只股票的模型...\n")
    
    results = []
    for symbol in symbols:
        print(f"训练 {symbol}:")
        
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT * FROM stock_prices WHERE symbol = ? ORDER BY date",
            conn, params=(symbol,)
        )
        conn.close()
        
        if len(df) < 50:
            print(f"  数据不足 ({len(df)} 条)，跳过")
            continue
        
        # 训练模型
        price_result = train_price_model(symbol, df)
        trend_result = train_trend_model(symbol, df)
        
        if price_result and trend_result:
            model, importance = price_result
            print(f"  重要特征: {importance.iloc[0]['feature']} ({importance.iloc[0]['importance']:.2%})")
            results.append({
                'symbol': symbol,
                'price_rmse': np.sqrt(mean_squared_error(
                    price_result[0].predict(prepare_features(df).drop(['target_price', 'target_trend'], axis=1)),
                    prepare_features(df)['target_price']
                )),
                'trend_accuracy': trend_result[1]
            })
    
    print("\n训练完成！")
    return results

def generate_predictions():
    """生成预测"""
    conn = sqlite3.connect(DB_PATH)
    symbols = pd.read_sql_query(
        "SELECT DISTINCT symbol FROM stock_prices", conn
    )['symbol'].tolist()
    conn.close()
    
    predictions = []
    for symbol in symbols:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT * FROM stock_prices WHERE symbol = ? ORDER BY date",
            conn, params=(symbol,)
        )
        conn.close()
        
        pred = predict_next_day(symbol, df)
        if pred:
            predictions.append(pred)
            
            # 存储预测结果
            conn = sqlite3.connect(DB_PATH)
            conn.execute('''
                INSERT INTO price_predictions
                (symbol, date, actual_close, predicted_close, prediction_date, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (pred['symbol'], pred['date'], pred['actual_close'], 
                  pred['predicted_close'], datetime.now().strftime('%Y-%m-%d'),
                  pred['confidence']))
            
            conn.execute('''
                INSERT INTO trend_predictions
                (symbol, date, predicted_trend, up_probability, down_probability, 
                 prediction_date, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (pred['symbol'], pred['date'], pred['predicted_trend'],
                  pred['up_probability'], pred['down_probability'],
                  datetime.now().strftime('%Y-%m-%d'), pred['confidence']))
            conn.commit()
            conn.close()
    
    return predictions

def show_predictions():
    """显示预测结果"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT p.symbol, p.date, p.actual_close, p.predicted_close,
               t.predicted_trend, t.up_probability, p.confidence
        FROM price_predictions p
        JOIN trend_predictions t ON p.symbol = p.symbol AND p.date = t.date
        WHERE p.prediction_date = (SELECT MAX(prediction_date) FROM price_predictions)
        GROUP BY p.symbol
    ''', conn)
    conn.close()
    
    if df.empty:
        print("暂无预测结果")
    else:
        print("\n最新预测:")
        print(df.to_string(index=False))

if __name__ == "__main__":
    import sys
    
    init_prediction_tables()
    
    if len(sys.argv) > 1 and sys.argv[1] == "train":
        train_all_models()
    elif len(sys.argv) > 1 and sys.argv[1] == "predict":
        predictions = generate_predictions()
        for p in predictions:
            print(f"\n{p['symbol']}:")
            print(f"  当前: {p['actual_close']:.2f}")
            print(f"  预测: {p['predicted_close']:.2f} ({p['predicted_change_pct']:+.2f}%)")
            print(f"  趋势: {p['predicted_trend']} (置信度: {p['confidence']:.1%})")
    elif len(sys.argv) > 1 and sys.argv[1] == "show":
        show_predictions()
    else:
        print("用法: python3 stock_predictor.py [train|predict|show]")
