# 机票价格监控 - 广州到青岛

## 需求
- 航线：广州(CAN) → 青岛(TAO)
- 舱位：经济舱
- 单程
- 监控未来30天
- 低价阈值：¥500（不含税）
- 通知：Discord

## 数据源优先级
1. Skyscanner（国际版，反爬相对宽松）
2. 携程国际版 (Trip.com)
3. 去哪儿（如前面失败）

## 技术栈
- Scrapling：抓取 + 反爬绕过
- 飞书多维表格：数据存储
- OpenClaw Cron：定时执行
- Discord：低价提醒

## 文件结构
```
flight-monitor/
├── plan.md           # 本文件
├── config.py         # 配置（航线、阈值等）
├── fetcher.py        # 抓取逻辑
├── parser.py         # 数据解析
├── storage.py        # 飞书表格操作
├── notifier.py       # Discord 通知
├── main.py           # 主入口
└── test_fetch.py     # 测试抓取
```

## 执行步骤
1. [ ] 测试 Skyscanner 抓取可行性
2. [ ] 创建飞书多维表格存储价格数据
3. [ ] 实现抓取 + 解析逻辑
4. [ ] 实现价格对比 + 通知逻辑
5. [ ] 设置定时任务
