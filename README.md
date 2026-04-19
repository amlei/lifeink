> Saving data of the books and videos into the notion page with Python.

>使用Python将图书和影视数据存放入Notion中。



# 🖼️介绍

## 环境

- Python 3.10+ （建议 3.11 及以上）
- Pycharm / Vs Code / Vs Code Studio

## 项目结构

```
│  .env
│  main.py - 主函数、执行程序
│  new_book.txt - 上一次更新书籍
│  new_video.txt - 上一次更新影视
│  README.md
│  requirements.txt - 依赖库
│
├─assets - README.md文件
│
├─function - 其它功能函数
│  │  glo.py - 全局数据
│  │  spider.py - 爬取个人豆瓣数据
│  │  __init__.py
│
├─icon - 图标
│       book.svg
│       movie.svg
│       video.svg
│
├─docs - 文档
│
└─src - 新功能模块（独立 uv 项目，不影响原有实现）
   └─feature
      └─feature/community
         ├─douban - 豆瓣数据抓取（Playwright）
         ├─weread - 微信读书（待开发）
         └─flomo  - Flomo（待开发）
```

---

# 🐾 步骤

1. [Notion API创建](https://www.notion.so/Notion-93ad50c4bcc34c608fdc1fe211d6b322?pvs=21)
2. [数据爬取](https://www.notion.so/Notion-93ad50c4bcc34c608fdc1fe211d6b322?pvs=21)
3. 更新入Notion

## 🕷️ 网页数据

- 头文件
  - URL
  - Cookie
  - User-Agent
- 图书
  - 书名
  - 图像
  - 作者
  - 出版日期
  - 出版社
  - 标记数据
  - 短评
- 影视
  - 影片名
  - 图像
  - 上映日期
  - 标记数据



## 🤖 Notion

- [获得Token码](https://www.notion.so/Notion-18d07bcc24d54bddb97110814b23ddb6?pvs=21)
- 获得数据库页面ID并链接
- 存入数据



# 🎢 特征

## [豆瓣网](https://www.douban.com/)数据

- [x] 数据图像
- [x] 翻页数据提取
- [x] 增量更新

## 存入 Notion

- [x] 图标
- [x] 图像
- [x] 评星

## 新版抓取（`src/feature/`）

基于 Playwright 的独立模块，使用 uv 管理依赖，不依赖原有 requests 方案。

- [x] 自动登录检测（session 过期自动弹出二维码）
- [x] 豆瓣：图书、影视、游戏、书评、日记、个人资料
- [ ] 微信读书（weread）
- [ ] Flomo

详见 [src/feature/README.md](./src/feature/README.md)。

---

# 📋 Todo

## 数据源

- [ ] 微信读书（weread）数据抓取
- [ ] Flomo 数据抓取

## Agent 个人信息平台可视化

- [ ] 统一数据模型（豆瓣 + 微信读书 + Flomo）
- [ ] 个人信息看板：阅读统计、观影记录、想法时间线
- [ ] 数据聚合与筛选

## 数据可视化

- [ ] 阅读趋势图表（月度/年度统计）
- [ ] 书影音评分分布
- [ ] 标签词云与分类统计

## AI 生成记录报告

- [ ] 基于抓取数据自动生成周报/月报/年报
- [ ] AI 分析阅读偏好与推荐
- [ ] 导出为 Markdown / PDF



# 🤖行动

## 1. 准备阶段

拥有[豆瓣](https://www.douban.com/)和[Notion](https://www.notion.so/)账户。

![image-20230612163511339](./assets/image-20230612163511339.png)

## 2. 修改必要数据

下载好源码后解压进入目录，执行以下步骤：（[点击下载](https://github.com/amlei/Use-NotionAPI/archive/refs/heads/main.zip)）

1. 安装依赖

```powershell
pip install -r rerequirements.txt
```



2. 打开 `new_book.txt` 与 `new_video.txt` 更改你的 Notion 页面中最新的标记数据

3. 打开 `.env` 文件，修改必要参数

<img src="./assets/image-20240313172916768.png" alt="image-20240313172916768" style="zoom:25%;" />

4. 运行 `main.py` 文件

<img src="./assets/image-20240313172931685.png" alt="image-20240313172931685" style="zoom: 15%;" />

![result](./assets/result.png)

# 🔗其它链接

[Notion API的使用——获取豆瓣书影数据更新入Notion数据库_哔哩哔哩](https://www.bilibili.com/video/BV15o4y1W7hw/?spm_id_from=333.999.0.0)

[创建 Notion API](https://www.notion.so/my-integrations)

[Notion API使用思路](https://www.notion.so/yapotato/Notion-API-ChatGPT-93ad50c4bcc34c608fdc1fe211d6b322?pvs=4)
