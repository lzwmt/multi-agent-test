# 机票价格监控

广州 → 青岛 航线价格监控系统

## 功能

- ✅ 自动抓取 Skyscanner 机票价格
- ✅ 飞书多维表格存储历史数据
- ✅ Discord 低价提醒
- ✅ 定时任务自动执行

## 配置

编辑 `config.py` 修改：

```python
ORIGIN_CODE = "CAN"      # 出发机场
DESTINATION_CODE = "TAO"  # 到达机场
PRICE_THRESHOLD = 500     # 低价阈值（CNY）
DAYS_AHEAD = 30           # 监控天数
```

## 使用

### 手动运行

```bash
cd /root/.openclaw/workspace/projects/flight-monitor
source ~/.venvs/scrapling/bin/activate
python run.py
```

### 定时任务

已配置 OpenClaw Cron，每天上午 9 点自动执行。

## 文件结构

```
flight-monitor/
├── README.md       # 本文件
├── config.py       # 配置
├── fetcher_v2.py   # 抓取模块
├── storage.py      # 存储模块
├── notifier.py     # 通知模块
├── run.py          # 主程序
└── test_fetch.py   # 测试脚本
```

## 数据源

- Skyscanner（国际版）
- 价格货币：SGD（新加坡元），自动转换为 CNY
- 汇率：1 SGD ≈ 5.4 CNY

## 通知规则

- **低价提醒**：当发现价格 ≤ 阈值时，立即发送 Discord 通知
- **每日报告**：无低价时，发送当日价格汇总报告

## 飞书表格

多维表格 URL: https://my.feishu.cn/base/YgZlbTL1kaCxhjsc0TgcfdO7ned

包含字段：
- 日期
- 价格（原货币）
- 货币
- 数据源
- 抓取时间
- 航线
- 价格 CNY（转换后）
