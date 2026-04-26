# Backend

基于 FastAPI + Playwright 的社区数据抓取与 API 服务模块，独立管理依赖。

## 环境要求

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## 快速开始

```bash
cd backend

# 安装依赖
uv sync

# 安装浏览器（首次）
uv run python -m playwright install chromium

# 配置 SMTP（注册功能需要）
cp config-example.yaml config.yaml
# 编辑 config.yaml 填入 SMTP 凭据

# 启动 API 服务
uv run python src/api.py

# 或使用 CLI 抓取数据
uv run python __main__.py --type books --pages 3
```

## API 服务

启动后默认监听 `http://localhost:8000`，Swagger 文档在 `/docs`。

### 认证

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 发送邮箱验证码 |
| `/api/auth/verify` | POST | 验证码校验 + 创建账号（返回 JWT） |
| `/api/auth/login` | POST | 登录（返回 JWT） |
| `/api/auth/me` | GET | 获取当前用户信息 |
| `/api/auth/me` | PUT | 更新用户资料 |
| `/api/auth/change-password` | POST | 修改密码 |
| `/api/auth/delete` | POST | 注销账号（软删除） |

使用 JWT Bearer Token 认证。`/api/auth/register`、`/api/auth/verify`、`/api/auth/login`、`/api/chat` 无需认证。

### 社区数据

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 流式聊天响应 |
| `/api/community/bind` | POST | 平台绑定操作（query: `action`, `platform`） |
| `/api/community/sync` | POST | 触发已绑定平台的数据同步 |
| `/api/community/ws` | WS | 绑定/同步进度实时推送（query: `token`） |
| `/api/community/data` | GET | 获取已同步的图书、影视、日记数据 |

`action` 可选值: `status`, `start`, `refresh`, `delete`。当前仅支持 `platform=douban`。

## CLI 抓取

```bash
uv run python __main__.py --type <类型> [--pages <页数>]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | 抓取类型：`profile` `books` `movies` `games` `reviews` `notes` `browser` | 必填 |
| `--pages` | 最大抓取页数 | 1 |

`browser` 类型会使用已保存的 session 打开一个交互式 Chromium 浏览器，方便调试或手动登录。

## 测试

```bash
uv run pytest tests/ -v -s
```

测试使用真实 Chromium 浏览器，首次运行需要扫码登录。

## 项目结构

```
backend/
  pyproject.toml
  config-example.yaml               # SMTP 配置模板
  __main__.py                       # CLI 入口
  src/
    api.py                          # FastAPI 应用（路由、WebSocket）
    api/
      douban.py                     # 豆瓣平台绑定逻辑（AsyncBindManager）
    core/
      auth/
        auth.py                     # JWT 创建/验证、密码哈希、验证码生成
        deps.py                     # get_current_user 依赖注入
        repository.py               # AuthRepo（用户、验证码 CRUD）
        routes.py                   /api/auth/* 路由
      middleware.py                 # AuthMiddleware（全局 JWT 校验）
      utils/
        config.py                   # config.yaml 加载（SmtpConfig）
        email.py                    # SMTP 邮件发送
    community/
      douban/
        client.py                   # DoubanClient（上下文管理器）
        session.py                  # Session 管理（加载/保存 cookies）
        login.py                    # 二维码登录流程
        models/                     # Pydantic 数据模型
        scrapers/                   # 页面抓取器（base.py 为分页基类）
      weread/                       # 微信读书（待开发）
      flomo/                        # Flomo（待开发）
  db/
    engine.py                       # SQLAlchemy 异步引擎、会话工厂
    base.py                         # DeclarativeBase
    models.py                       # ORM 模型（User, VerificationCode, CommunityMeta, BookRow 等）
    repository.py                   # 数据访问层（AuthRepo, CommunityMetaRepo, DataRepo）
  tests/
    test_login_integration.py       # 登录集成测试
```

## 编程使用

```python
from src.community.douban import DoubanClient

with DoubanClient() as client:
    client.ensure_ready()
    print(client.user_id)

    books = client.scrape_books(max_pages=2)
    for book in books:
        print(book.title, book.rating)
```
