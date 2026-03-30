"""机票监控配置"""

# 航线配置
ORIGIN = "广州"
ORIGIN_CODE = "CAN"  # 广州白云机场代码
DESTINATION = "青岛"
DESTINATION_CODE = "TAO"  # 青岛胶东机场代码

# 监控配置
DAYS_AHEAD = 30  # 监控未来30天
PRICE_THRESHOLD = 500  # 低价阈值（元，不含税）
CABIN_CLASS = "经济舱"

# 数据源配置
DATA_SOURCES = [
    {
        "name": "skyscanner",
        "enabled": True,
        "base_url": "https://www.skyscanner.com",
    },
    {
        "name": "trip",
        "enabled": True,
        "base_url": "https://www.trip.com",
    },
]

# Discord 通知配置
DISCORD_CHANNEL = "#main"  # 或指定频道ID

# 飞书多维表格配置
BITABLE_NAME = "机票价格监控"
TABLE_NAME = "广州青岛航线"
