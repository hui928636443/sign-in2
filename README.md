# 个人学习项目
## 还在开发中

## LinuxDO 配置说明

### 登录方式

支持三种登录方式（按优先级）：

1. **Cookie 模式**（推荐，最稳定）
2. **缓存 Cookie**（自动保存上次登录的 Cookie）
3. **浏览器登录**（用户名密码）

### 配置示例

```json
// LINUXDO_ACCOUNTS 环境变量
[
  {
    "name": "主账号",
    "username": "your_username",
    "password": "your_password",
    "browse_enabled": true,
    "level": 2
  },
  {
    "name": "Cookie模式账号",
    "cookies": "_forum_session=xxx; _t=xxx; cf_clearance=xxx",
    "browse_enabled": true,
    "level": 3
  }
]
```

### 获取 Cookie

1. 在浏览器中登录 linux.do
2. 按 F12 打开开发者工具
3. 进入 Application → Cookies → linux.do
4. 复制 `_forum_session`、`_t`、`cf_clearance` 的值

### Level 说明

- `level: 1` - 慢速浏览，多看一些时间，浏览 10 个帖子
- `level: 2` - 正常浏览，一般时间，浏览 7 个帖子
- `level: 3` - 快速浏览，看一会儿就结束，浏览 5 个帖子