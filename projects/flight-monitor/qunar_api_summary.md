# 去哪儿 API 接口梳理

## 已发现的接口

### 1. getAsyncPrice - 特价价格接口

**URL:** `POST https://m.flight.qunar.com/lowFlightInterface/api/getAsyncPrice`

**请求参数:**
```json
{
  "b": {
    "timeout": 5000,
    "simpleData": "yes",
    "t": "f_urInfo_superLow_async",
    "flightInfo": [
      {
        "flightCode": "CAN_TAO_2026-03-14",
        "price": "",
        "jumpUrl": ""
      }
    ]
  }
}
```

**返回数据:**
```json
{
  "data": {
    "asyncResultMap": {
      "CAN_TAO_2026-03-14": {
        "flightCode": "CAN_TAO_2026-03-14",
        "price": "869",
        "jumpUrl": "https://touch.qunar.com/lowFlight/flightList?..."
      }
    }
  }
}
```

**数据字段:**
| 字段 | 说明 | 示例 |
|------|------|------|
| flightCode | 航线代码 | "CAN_TAO_2026-03-14" |
| price | 最低价格 | "869" |
| jumpUrl | 跳转链接 | 完整URL |

**获取方式:** 直接 POST 调用，无需登录

**限制:**
- ✅ 可获取指定航线价格
- ❌ 无航班号
- ❌ 无起飞/降落时间
- ⚠️ 返回的是特价推荐，可能包含多条航线

---

### 2. getAirLine - 推荐航线接口

**URL:** `POST https://m.flight.qunar.com/lowFlightInterface/api/getAirLine`

**请求参数:**
```json
{
  "b": {
    "locationAirCity": "北京",
    "locationCity": "北京",
    "timeout": 5000,
    "holiday": "default",
    "simpleData": "yes",
    "t": "f_urInfo_superLow_data",
    "cat": "touch_flight_home",
    "tabName": ""
  },
  "c": {}
}
```

**返回数据:**
```json
{
  "data": {
    "domList": [
      {
        "flightNo": "9C7515",
        "depTime": "2026-03-16 20:10",
        "arrTime": "2026-03-16 22:40",
        "flightTime": "2h30m",
        "price": 210,
        "depCity": "北京",
        "arrCity": "兰州",
        "flightTypeDesc": "直飞",
        "date": "2026-03-16"
      }
    ]
  }
}
```

**数据字段:**
| 字段 | 说明 | 示例 |
|------|------|------|
| flightNo | 航班号 | "9C7515" |
| depTime | 起飞时间 | "2026-03-16 20:10" |
| arrTime | 降落时间 | "2026-03-16 22:40" |
| flightTime | 飞行时长 | "2h30m" |
| price | 价格 | 210 |
| depCity | 出发城市 | "北京" |
| arrCity | 到达城市 | "兰州" |
| flightTypeDesc | 航班类型 | "直飞" |

**获取方式:** Playwright 劫持响应

**限制:**
- ✅ 有航班号、时间、价格
- ❌ 基于定位城市，非指定航线
- ❌ 返回的是推荐航线列表

---

### 3. priceCalendar - 价格日历接口

**URL:** `GET https://gw.flight.qunar.com/api/f/priceCalendar`

**请求参数:**
```
?dep=广州&arr=青岛
```

**返回数据:**
```json
{
  "data": {
    "bflights": [
      {
        "date": "2026-03-12",
        "price": "",
        "priceDesc": "查价"
      }
    ]
  }
}
```

**数据字段:**
| 字段 | 说明 | 示例 |
|------|------|------|
| date | 日期 | "2026-03-12" |
| price | 价格 | "" (空) |
| priceDesc | 价格描述 | "查价" |

**获取方式:** 直接 GET 调用

**限制:**
- ✅ 可获取日期列表
- ❌ 价格字段为空
- ❌ 无航班详情

---

### 4. touchInnerList - 航班列表接口

**URL:** `POST https://m.flight.qunar.com/touchInnerList`

**请求参数:**
```json
{
  "depCity": "北京",
  "arrCity": "上海",
  "goDate": "2026-03-13",
  "baby": "0",
  "cabinType": "0",
  "child": "0",
  "from": "touch_index_search",
  "firstRequest": "true",
  "Bella": "1683616182042##..."  // 加密签名
}
```

**返回数据:** HTML 页面 (非 JSON)

**获取方式:** 需要 Playwright 或正确签名

**限制:**
- ❌ 需要 `Bella` 签名参数
- ❌ 直接调用返回 HTML
- ⚠️ 可能包含完整航班数据

---

## 数据对比

| 接口 | 价格 | 航班号 | 时间 | 指定航线 | 调用难度 |
|------|------|--------|------|----------|----------|
| getAsyncPrice | ✅ | ❌ | ❌ | ✅ | 低 |
| getAirLine | ✅ | ✅ | ✅ | ❌ | 中 |
| priceCalendar | ❌ | ❌ | ❌ | ✅ | 低 |
| touchInnerList | ? | ? | ? | ✅ | 高 |

---

## 结论

### 可用方案

**方案1: 仅使用 getAsyncPrice**
- ✅ 可获取指定航线动态价格
- ❌ 无航班号和时间
- 适用: 纯价格监控

**方案2: 使用 getAirLine**
- ✅ 有完整航班数据
- ❌ 非指定航线
- 适用: 推荐航线查看

**方案3: 整合携程 + 去哪儿**
- ✅ 携程: 价格 + 航班号 + 时间
- ✅ 去哪儿: 额外价格参考
- 适用: 完整监控系统

### 建议

**推荐方案3: 以携程为主，去哪儿为辅**
- 携程: 主数据源（完整可靠）
- 去哪儿: 价格对比（getAsyncPrice）
