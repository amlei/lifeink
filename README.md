# LifeInk AI

> Personal AI Agent - 聚合书影音日记，用 AI 重新理解你的生活。

LifeInk AI 从豆瓣、微信读书、Flomo 等平台采集个人的阅读、影视、游戏、日记等数据，通过 AI 进行对话分析、偏好洞察，并自动生成周报/月报/年度总结。

---

## 当前状态

### 数据源

- [x] 豆瓣 - 图书、影视、游戏、书评、日记、个人资料（Playwright）
- [x] 豆瓣 - 图书、影视同步至 Notion（requests）
- [ ] 微信读书（weread）
- [ ] Flomo

### 数据同步

- [x] 增量同步至 Notion 数据库
- [x] 自动登录检测（session 过期弹二维码）
- [x] 翻页数据提取、图标/封面/评分
- [x] 本地 SQLite 数据库存储（SQLAlchemy async）
- [x] 绑定后自动抓取图书和影视数据

### AI 对话

- [x] 前端聊天界面（React + Vite）
- [x] 流式响应（StreamingResponse + AI SDK）
- [ ] 接入 LLM 提供商

---

## 项目结构

```
main.py              # Notion 同步入口（legacy）
function/
  glo.py             # 全局配置
  spider.py          # 豆瓣数据爬取（requests）
json/                # Notion 数据库模板
icon/                # 页面图标

backend/             # API 服务 + 数据抓取（uv 独立项目）
  src/api.py         # FastAPI 应用（路由、WebSocket）
  src/api/douban.py  # 豆瓣平台绑定逻辑（AsyncBindManager）
  src/community/     # 社区数据源
    douban/          # 豆瓣（Playwright 登录 + requests 抓取）
    weread/          # 微信读书（待开发）
    flomo/           # Flomo（待开发）
  db/                # SQLAlchemy 异步数据库层（SQLite）
  tests/             # pytest 测试

frontend/            # React 聊天界面（Bun + Vite）
  src/api/douban.ts  # 豆瓣 API 集成（REST + WebSocket）
  src/components/    # UI 组件（Sidebar, ChatPanel, ProfileModal 等）
  src/hooks/         # 自定义 Hook（useChatStore）
```

---

## 快速开始

### 一键启动

```bash
./start.sh
```

启动后：
- 前端: http://localhost:5173
- 后端: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 后端单独启动

```bash
cd backend
uv sync
uv run python -m playwright install chromium  # 首次
uv run python src/api.py
```

详见 [backend/README.md](./backend/README.md)。

### Notion 同步（原有功能）

```bash
pip install -r requirements.txt
# 配置 .env（TOKEN、DATABASE_ID、COOKIE 等）
python main.py
```

---

## Roadmap

### Phase 1 - 数据采集 (current)

- [x] 豆瓣全量数据抓取
- [x] 本地数据持久化
- [ ] 微信读书数据接入
- [ ] Flomo 数据接入

### Phase 2 - AI Agent

- [ ] AI 对话接口（基于个人数据上下文）
- [ ] 阅读偏好分析与推荐
- [ ] 标签/分类智能整理
- [ ] 跨平台数据关联（读书笔记 vs 影评 vs 日记）

### Phase 3 - 自动报告

- [ ] 周报/月报/年报自动生成
- [ ] Markdown / PDF / Web 导出
- [ ] 报告模板自定义

### Phase 4 - 可视化看板

- [ ] 个人信息看板（阅读统计、观影记录、想法时间线）
- [ ] 阅读趋势图表（月度/年度）
- [ ] 书影音评分分布
- [ ] 标签词云与分类统计

---

## 参考

- [Notion API](https://www.notion.so/my-integrations)
- [Playwright](https://playwright.dev/python/)
- [Vercel AI SDK](https://sdk.vercel.ai/)
