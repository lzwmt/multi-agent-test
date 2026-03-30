---
name: gog-oauth
description: Google OAuth 授权流程指南。用于 gog CLI 工具的 Gmail/日历/Drive 等 Google 服务的授权设置和故障排查。当用户需要设置 gog 授权、处理 OAuth 回调、解决授权过期或导入 token 时使用。
---

# gog OAuth 授权指南

## 快速参考

### 环境变量设置
```bash
export GOG_KEYRING_PASSWORD=openclaw
export GOG_ACCOUNT=lzwmt118@gmail.com
```

### 常用命令
```bash
# 查看已授权账户
gog auth list

# 查看授权状态
gog status

# 测试 Gmail 连接
gog gmail search 'newer_than:1d' --max 5
```

---

## 授权流程

### 1. 首次授权

如果还没有 OAuth 客户端凭证，先设置：
```bash
gog auth credentials /path/to/client_secret.json
```

启动授权流程：
```bash
gog auth add lzwmt118@gmail.com --services gmail,calendar,drive,contacts,sheets,docs
```

浏览器会打开 Google 授权页面，完成授权后会跳转到本地回调地址（如 `http://127.0.0.1:xxxx/oauth2/callback?...`）。

### 2. 处理回调

复制完整的回调 URL，提取授权码：
```bash
# 从回调 URL 中提取 code 参数
code=$(echo "$callback_url" | grep -o 'code=[^&]*' | cut -d'=' -f2)
```

用授权码换取 token：
```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=$code" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=http://127.0.0.1:42941/oauth2/callback"
```

### 3. 导入 Token

创建 token 导入文件：
```bash
cat > /tmp/token_export.json << 'EOF'
{
  "email": "lzwmt118@gmail.com",
  "refresh_token": "1//...",
  "scopes": [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents"
  ]
}
EOF
```

导入 token：
```bash
gog auth tokens import /tmp/token_export.json
```

---

## 故障排查

### 问题：授权码过期
**错误：** `invalid_grant: Bad Request`

**原因：** Google 授权码只能使用一次且有效期很短（几分钟）。

**解决：** 重新走授权流程，获取新的回调 URL。

### 问题：邮箱不匹配
**现象：** 授权成功但 gog 提示 `No auth for...`

**原因：** 授权的 Google 账户与 gog 配置的邮箱不一致。

**解决：** 
1. 检查当前配置的邮箱：`ls ~/.config/gogcli/keyring/`
2. 删除错误的 token 文件
3. 重新导入正确邮箱的 token

### 问题：需要重复输入密码
**解决：** 设置环境变量避免交互式密码输入：
```bash
export GOG_KEYRING_PASSWORD=openclaw
```

---

## Token 有效期

| Token 类型 | 有效期 | 说明 |
|-----------|--------|------|
| Access token | 1 小时 | 自动刷新，无需干预 |
| Refresh token | 7 天（可续期） | 长期使用，自动续期 |

**注意：** 只要正常使用，refresh token 可以长期有效。以下情况需要重新授权：
- 主动撤销 Google 账户中的应用权限
- 修改 Google 账户密码
- 长时间（几个月）未使用

---

## 文件位置

```
~/.config/gogcli/
├── config.json          # 配置文件（keyring 后端设置）
├── credentials.json     # OAuth 客户端凭证
└── keyring/
    └── lzwmt118@gmail.com    # 加密的 token 文件
```

---

## 完整示例：授权流程

```bash
# 1. 启动授权（获取回调 URL）
gog auth add lzwmt118@gmail.com --services gmail,calendar,drive,contacts,sheets,docs

# 2. 用户完成浏览器授权后，会跳转到类似：
# http://127.0.0.1:42941/oauth2/callback?state=xxx&code=4/0A...&scope=...

# 3. 用回调 URL 中的 code 换取 token（curl 命令见上文）

# 4. 创建 token 导入文件并导入
cat > /tmp/token.json << 'EOF'
{"email": "lzwmt118@gmail.com", "refresh_token": "1//...", "scopes": [...]}
EOF
gog auth tokens import /tmp/token.json

# 5. 验证
export GOG_KEYRING_PASSWORD=openclaw
gog auth list
gog gmail search 'newer_than:1d' --max 5
```
