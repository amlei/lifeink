# Feature Module

基于 Playwright 的社区数据抓取模块，与项目原有实现隔离，独立管理依赖。

## 环境要求

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## 快速开始

```bash
cd src/feature

# 安装依赖
uv sync

# 安装浏览器（首次）
uv run python -m playwright install chromium

# 抓取数据（自动判断登录状态，session 过期会弹出二维码）
uv run python -m feature --type books --pages 3
```

## 命令行

```bash
uv run python -m feature --type <类型> [--pages <页数>]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | 抓取类型：`profile` `books` `movies` `games` `reviews` `notes` | 必填 |
| `--pages` | 最大抓取页数 | 1 |

## 工作流程

1. 启动浏览器，加载已保存的 session（`.playwright/douban-state.json`）
2. 访问豆瓣首页，检查登录状态
3. 已登录 -> 自动获取 user_id，开始抓取
4. 未登录 -> 弹出浏览器显示二维码，扫码后继续
5. 抓取完成，session 自动保存回磁盘

## 项目结构

```
feature/
  pyproject.toml
  feature/
    __main__.py                    # CLI 入口
    community/
      douban/
        client.py                  # DoubanClient（上下文管理器）
        session.py                 # Session 管理（加载/保存 cookies）
        login.py                   # 二维码登录流程
        models/                    # Pydantic 数据模型
          book.py, movie.py, game.py, review.py, note.py, profile.py
        scrapers/                  # 页面抓取器
          base.py                  # 分页基类
          books.py, movies.py, games.py, reviews.py, notes.py, profile.py
      weread/                      # 微信读书（待开发）
      flomo/                       # Flomo（待开发）
```

## 编程使用

```python
from feature.community.douban import DoubanClient

with DoubanClient() as client:
    client.ensure_ready()
    print(client.user_id)

    books = client.scrape_books(max_pages=2)
    for book in books:
        print(book.title, book.rating)
```
