# 浏览器自动化测试项目

测试 OpenClaw 2026.3.13 浏览器功能更新：
- Chrome DevTools MCP 附加模式
- profile="user" 和 profile="chrome-relay"
- 批量操作、选择器定位、延迟点击

## 测试用例

1. **基础导航** - 访问网页并截图
2. **元素交互** - 点击、输入、表单提交
3. **批量操作** - 多步骤自动化
4. **选择器定位** - CSS/XPath 定位元素
5. **延迟点击** - 带延迟的交互

## 运行

```bash
openclaw run test-basic.js
```
