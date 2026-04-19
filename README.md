# LifeInk AI

> Personal AI Agent - 聚合书影音日记，用 AI 重新理解你的生活。

LifeInk AI 从豆瓣、微信读书、Flomo 等平台采集个人的阅读、影视、游戏、日记等数据，通过 AI 进行对话分析、偏好洞察，并自动生成周报/月报/年度总结。

---

## 愿景

让每个人的生活记录不再是沉睡的数据，而是可以被理解、回顾和重新发现的记忆。

### 核心能力

- **数据聚合** - 统一采集多平台个人数据（书影音、日记、想法）
- **AI 对话** - 基于个人数据与 AI 自由对话，获取洞察与推荐
- **自动报告** - 周报、月报、年报自动生成，支持 Markdown / PDF / Web 导出
- **数据可视化** - 阅读趋势、评分分布、标签云、时间线看板

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

---

## 项目结构

```
 main.py              - Notion 同步入口
 function/
   glo.py             - 全局配置
   spider.py          - 豆瓣数据爬取（requests）
 json/                - Notion 数据库模板
 icon/                - 页面图标

 docs/                - 文档

 src/feature/         - 新版模块（uv 独立项目）
   feature/community/
     douban/          - 豆瓣数据抓取（Playwright）
       models/        - 数据模型（Pydantic）
       scrapers/      - 各类型抓取器
       client.py      - API 客户端
       login.py       - 登录管理
       session.py     - 会话持久化
     weread/          - 微信读书（待开发）
     flomo/           - Flomo（待开发）
```

---

## 快速开始

### Notion 同步（原有功能）

1. 安装依赖：`pip install -r requirements.txt`
2. 配置 `.env`（TOKEN、DATABASE_ID、COOKIE 等）
3. 运行 `python main.py`

### Playwright 抓取（新版模块）

```bash
cd src/feature
uv sync
uv run python -m feature
```

详见 [src/feature/README.md](./src/feature/README.md)。

---

## Roadmap

### Phase 1 - 数据采集 (current)

- [x] 豆瓣全量数据抓取
- [ ] 微信读书数据接入
- [ ] Flomo 数据接入
- [ ] 统一数据模型与存储层

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
- [Notion API 使用教程 - Bilibili](https://www.bilibili.com/video/BV15o4y1W7hw/)
- [Playwright](https://playwright.dev/python/)
