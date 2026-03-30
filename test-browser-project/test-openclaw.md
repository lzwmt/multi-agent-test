# OpenClaw 浏览器测试

使用 OpenClaw 内置 browser 工具运行测试。

## 测试 1: 基础导航

访问 example.com 并截图：

```
/browser open url:"https://example.com"
/browser act kind:wait timeMs:1000
/browser screenshot fullPage:true
/browser snapshot
```

## 测试 2: GitHub 页面（测试 profile=user）

```
/browser open url:"https://github.com" profile:user
/browser act kind:wait timeMs:2000
/browser snapshot
```

## 测试 3: 元素交互测试

访问 httpbin 表单：

```
/browser open url:"https://httpbin.org/forms/post"
/browser act kind:wait timeMs:2000
/browser snapshot interactive:true
```

## 测试 4: 批量操作

```
/browser open url:"https://example.com"
/browser act kind:evaluate fn:"() => ({ title: document.title, url: window.location.href })"
```

## 测试 5: 选择器定位

```
/browser open url:"https://example.com"
/browser snapshot refs:aria
```
