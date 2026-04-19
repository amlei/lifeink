# Douban Playwright Data Scraping

Using Playwright CLI to log in and scrape personal Douban data.

## Environment Setup

```bash
# Global install
npm install -g @playwright/cli@latest
playwright-cli install

# Project dependency (for image processing)
uv pip install Pillow
```

Config file auto-generated at `.playwright/cli.config.json`.
Session state file at `.playwright/douban-state.json` (gitignored, contains cookies).

## 0. Session State Persistence

### Save state (after login)

```bash
playwright-cli state-save .playwright/douban-state.json
```

### Load state (reuse login, skip QR scan)

```bash
playwright-cli state-load .playwright/douban-state.json
```

### Python (Playwright library, for development/deployment)

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # Load saved state (cookies + localStorage)
    context = browser.new_context(storage_state=".playwright/douban-state.json")
    page = context.new_page()
    page.goto("https://www.douban.com/people/{AccountID}/")
    # Already logged in, no QR scan needed

    # ... scrape data ...

    # Optionally save updated state back
    context.storage_state(path=".playwright/douban-state.json")
    browser.close()
```

### State file contents

`.playwright/douban-state.json` contains:
- `cookies` -- Douban session cookies (bid, dbcl2, ck, etc.)
- `origins` -- localStorage entries

The file is excluded from git via `.gitignore` (`.playwright`). When cookies expire, re-login and re-save.

## 1. Login (QR Code)

### Open login page (headed mode)

```bash
playwright-cli open "https://accounts.douban.com/passport/login" --headed
```

### Switch to QR code login

The page defaults to SMS login. Click the icon in the top-right corner to switch:

```js
// Click the switch icon to enter QR login mode
document.querySelector('.quick.icon-switch').click()
```

Page structure after switching:
- `listitem` containing "二维码登录"
- `img[alt="QR Code"]` -- the QR code image
- `link "短信验证登录"` -- link back to SMS login

### Capture and display QR code

```bash
# Screenshot the QR code element
playwright-cli screenshot <ref> --filename=douban-login-qr
```

Display via Pillow (recommended, scannable):

```python
from PIL import Image

img = Image.open('douban-login-qr')
img_large = img.resize((img.width * 4, img.height * 4), Image.NEAREST)
img_large.show(title='Douban QR Login')
```

### Post-login navigation

After scanning, page redirects to `https://www.douban.com/`. The top-right now shows account name link.

```js
// Click account name to expand menu
// Menu contains: 个人主页 / 我的订单 / 我的钱包 / 账号管理 / 退出
// Click "个人主页"
document.querySelector('a[href*="/mine/"]').click()
// Or directly navigate:
// https://www.douban.com/people/{userId}/
```

## 2. Personal Homepage Data

URL: `https://www.douban.com/people/{userId}/`

### 2.1 Profile Info

```js
(() => {
  const result = {};
  const infobox = document.querySelector('.infobox');
  result.avatar = infobox?.querySelector('img')?.src || null;
  result.bio = infobox?.textContent?.trim() || null;

  const sig = document.querySelector('#edit_signature');
  result.signature = sig?.textContent?.trim() || null;

  return JSON.stringify(result);
})()
```

Output example:
```json
{
  "avatar": "https://img1.doubanio.com/icon/ul215871379-9.jpg",
  "signature": "脑子饿的人可真没有东西吃了。",
  "bio": "为回归提供异常。有人问：你为什么一直在学习？..."
}
```

### 2.2 Notes (Diary)

URL: `https://www.douban.com/mine/notes` (same-page navigation)

```js
// Navigate
document.querySelector('a[href*="/mine/notes"]').click()
```

```js
(() => {
  const items = document.querySelectorAll('.note-container');
  const notes = [];
  items.forEach(item => {
    const titleEl = item.querySelector('a');
    notes.push({
      title: titleEl?.textContent?.trim(),
      url: titleEl?.href
    });
  });
  return JSON.stringify(notes);
})()
```

### 2.3 Reviews

URL: `https://www.douban.com/people/{userId}/reviews` (new tab)

```bash
playwright-cli tab-new "https://www.douban.com/people/{userId}/reviews"
```

```js
(() => {
  const items = document.querySelectorAll('.review-item');
  const review = items[0];
  const subjectImg = review.querySelector('.subject-img img');
  const h2a = review.querySelector('h2 a');
  const allText = review.textContent || '';
  const dateMatch = allText.match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);

  return JSON.stringify({
    subjectTitle: subjectImg?.getAttribute('title'),
    subjectUrl: review.querySelector('.subject-img')?.href,
    subjectImgUrl: subjectImg?.src,
    reviewTitle: h2a?.textContent?.trim(),
    reviewUrl: h2a?.href,
    date: dateMatch?.[1] || null
  });
})()
```

Output example:
```json
{
  "subjectTitle": "硬道理",
  "subjectUrl": "https://book.douban.com/subject/37472012/",
  "subjectImgUrl": "https://img1.doubanio.com/view/subject/m/public/s35266879.jpg",
  "reviewTitle": "从治理到责任",
  "reviewUrl": "https://book.douban.com/review/17504929/",
  "date": "2026-03-15 18:31:55"
}
```

Note: Reviews have no rating field. Pagination available via `reviews?start=10`, `reviews?start=20`, etc.

## 3. Books

URL: `https://book.douban.com/people/{userId}/collect`

```bash
playwright-cli tab-new "https://book.douban.com/people/{userId}/collect"
```

### Selector structure

Each book is a `.subject-item` containing:
- `.pic img` -- cover image
- `h2 a` -- title and link
- `.pub` -- metadata string: `author / translator / publisher / date / price`
- `[class*=rating]` -- rating span, class like `rating5-t` means 5 stars
- `.date` -- date read, text like "2026-04-05 读过"
- `.tags` -- tags, text like "标签: 历史"
- `.comment` -- short comment

### Extraction script

```js
(() => {
  const book = document.querySelectorAll('.subject-item')[0];
  const pubText = book.querySelector('.pub')?.textContent?.trim() || '';
  const pubParts = pubText.split(' / ').map(s => s.trim());

  // Smart parse: 5 parts = has translator; 4 parts = no translator
  let author, translator, publisher, pubDate, price;
  if (pubParts.length >= 5) {
    [author, translator, publisher, pubDate, price] = pubParts;
  } else if (pubParts.length === 4) {
    [author, , publisher, pubDate, price] = [pubParts[0], null, pubParts[1], pubParts[2], pubParts[3]];
    translator = null;
  } else {
    author = pubParts[0];
  }

  const ratingClass = book.querySelector('[class*=rating]')?.className || '';
  const rating = ratingClass.match(/rating(\d)/)?.[1] || null;

  return JSON.stringify({
    title: book.querySelector('h2 a')?.textContent?.trim()?.replace(/\n/g, ' ').replace(/\s+/g, ' '),
    url: book.querySelector('h2 a')?.href,
    cover: book.querySelector('.pic img')?.src,
    author,
    translator,
    publisher,
    pubDate,
    price,
    rating: rating ? parseInt(rating) : null,
    date: book.querySelector('.date')?.textContent?.replace(/\n/g, ' ').trim(),
    tags: book.querySelector('.tags')?.textContent?.replace('标签: ', '').trim(),
    comment: book.querySelector('.comment')?.textContent?.trim()
  });
})()
```

Output example:
```json
{
  "title": "翦商 : 殷周之变与华夏新生",
  "url": "https://book.douban.com/subject/36096304/",
  "cover": "https://img1.doubanio.com/view/subject/s/public/s34385069.jpg",
  "author": "李硕",
  "translator": null,
  "publisher": "广西师范大学出版社",
  "pubDate": "2022-10",
  "price": "99.00元",
  "rating": 5,
  "date": "2026-04-05 读过",
  "tags": "历史",
  "comment": null
}
```

## 4. Movies/TV

URL: `https://movie.douban.com/people/{userId}/collect`

```bash
playwright-cli tab-new "https://movie.douban.com/people/{userId}/collect"
```

### Selector structure

Each movie is a `.item` containing:
- `.pic img` -- poster
- `.title a` -- title (may include alternate names separated by ` / `)
- `.intro` -- metadata: `date(country) / actors / ...`
- `[class*=rating]` -- rating, class like `rating5-t`
- `.date` -- date watched
- `.tags` -- tags
- `.comment` -- short comment

### Extraction script

```js
(() => {
  const movie = document.querySelectorAll('.item')[0];
  const introText = movie.querySelector('.intro')?.textContent?.trim() || '';
  // Only take date/country info, exclude actor names
  const dateInfo = introText.split(' / ')[0];

  const ratingClass = movie.querySelector('[class*=rating]')?.className || '';
  const rating = ratingClass.match(/rating(\d)/)?.[1] || null;

  return JSON.stringify({
    title: movie.querySelector('.title a')?.textContent?.trim()?.replace(/\n/g, ' ').replace(/\s+/g, ' '),
    url: movie.querySelector('.title a')?.href,
    cover: movie.querySelector('.pic img')?.src,
    dateInfo,
    rating: rating ? parseInt(rating) : null,
    date: movie.querySelector('.date')?.textContent?.trim(),
    tags: movie.querySelector('.tags')?.textContent?.replace('标签: ', '').trim(),
    comment: movie.querySelector('.comment')?.textContent?.trim()
  });
})()
```

Output example:
```json
{
  "title": "葬送的芙莉莲 第二季 / 葬送のフリーレン 第2期 / Frieren: Beyond Journey's End Season 2",
  "url": "https://movie.douban.com/subject/36829083/",
  "cover": "https://img2.doubanio.com/view/photo/s_ratio_poster/public/p2925567021.webp",
  "dateInfo": "2026-01-16(日本)",
  "rating": 5,
  "date": "2026-04-04",
  "tags": "剧情 动漫",
  "comment": "继童年《火影忍者》后，最喜欢的动漫！啊？这就大结局了吗？邓肯，不要啊！"
}
```

## 5. Games

URL: `https://www.douban.com/people/{userId}/games?action=collect`

Note: Default `/games` shows "want to play". Must append `?action=collect` for "played".

### Selector structure

Each game is a `.common-item` containing:
- `.pic img` -- cover
- `.title a` -- title and link
- `.desc` -- metadata: `platform / genre / release date`
- `.rating-star` -- rating, class like `allstar50` = 5 stars
- `.date` -- date played
- `.tags` -- tags
- Comment is a plain `div` child of `.content` (not `.title`, `.desc`, or `.user-operation`)

### Extraction script

```js
(() => {
  const game = document.querySelectorAll('.common-item')[0];
  const ratingClass = game.querySelector('.rating-star')?.className || '';
  const rating = ratingClass.match(/allstar(\d)0/)?.[1] || null;

  // Comment: plain div child of .content, excluding known containers
  let comment = null;
  const contentDiv = game.querySelector('.content');
  if (contentDiv) {
    for (const child of contentDiv.children) {
      if (!child.classList.contains('title')
        && !child.classList.contains('desc')
        && !child.classList.contains('user-operation')
        && child.textContent?.trim()) {
        comment = child.textContent.trim();
        break;
      }
    }
  }

  return JSON.stringify({
    title: game.querySelector('.title a')?.textContent?.trim(),
    url: game.querySelector('.title a')?.href,
    cover: game.querySelector('.pic img')?.src,
    desc: game.querySelector('.desc')?.childNodes[0]?.textContent?.trim(),
    rating: rating ? parseInt(rating) : null,
    date: game.querySelector('.date')?.textContent?.trim(),
    tags: game.querySelector('.tags')?.textContent?.replace('标签: ', '').trim(),
    comment
  });
})()
```

Output example:
```json
{
  "title": "底特律：化身为人 Detroit: Become Human",
  "url": "https://www.douban.com/game/26652745/",
  "cover": "https://img3.doubanio.com/lpic/s29705432.jpg",
  "desc": "PC / PS4 / 射击 / 冒险 / 动作 / 2018-05-25 / 2018-05-25",
  "rating": 5,
  "date": "2025-02-03",
  "tags": "科幻",
  "comment": "两个人物被我玩趴😭还是最喜欢RK800"
}
```

## 6. Full JSON Output (First Item Per Category)

```json
{
  "profile": {
    "userId": "215871379",
    "username": "啊莱",
    "avatar": "https://img1.doubanio.com/icon/ul215871379-9.jpg",
    "signature": "脑子饿的人可真没有东西吃了。",
    "bio": "为回归提供异常。有人问：你为什么一直在学习？我笑笑没作回答。我知自己愚钝，要许久才能将新知识、新技能理解，只好下更大的功夫去钻研。我始终在与自己的思想作斗争，希冀寻找发光的星……",
    "joinDate": "2020-04-26",
    "location": "广东"
  },
  "notes": [
    { "title": "2026年3月17日", "url": "https://www.douban.com/topic/481243878/" }
  ],
  "reviews": [
    {
      "subjectTitle": "硬道理",
      "subjectUrl": "https://book.douban.com/subject/37472012/",
      "subjectImgUrl": "https://img1.doubanio.com/view/subject/m/public/s35266879.jpg",
      "reviewTitle": "从治理到责任",
      "reviewUrl": "https://book.douban.com/review/17504929/",
      "date": "2026-03-15 18:31:55"
    }
  ],
  "books": [
    {
      "title": "翦商 : 殷周之变与华夏新生",
      "url": "https://book.douban.com/subject/36096304/",
      "cover": "https://img1.doubanio.com/view/subject/s/public/s34385069.jpg",
      "author": "李硕",
      "translator": null,
      "publisher": "广西师范大学出版社",
      "pubDate": "2022-10",
      "price": "99.00元",
      "rating": 5,
      "date": "2026-04-05 读过",
      "tags": "历史",
      "comment": null
    }
  ],
  "movies": [
    {
      "title": "葬送的芙莉莲 第二季 / 葬送のフリーレン 第2期",
      "url": "https://movie.douban.com/subject/36829083/",
      "cover": "https://img2.doubanio.com/view/photo/s_ratio_poster/public/p2925567021.webp",
      "dateInfo": "2026-01-16(日本)",
      "rating": 5,
      "date": "2026-04-04",
      "tags": "剧情 动漫",
      "comment": "继童年《火影忍者》后，最喜欢的动漫！"
    }
  ],
  "games": [
    {
      "title": "底特律：化身为人 Detroit: Become Human",
      "url": "https://www.douban.com/game/26652745/",
      "cover": "https://img3.doubanio.com/lpic/s29705432.jpg",
      "desc": "PC / PS4 / 射击 / 冒险 / 动作 / 2018-05-25",
      "rating": 5,
      "date": "2025-02-03",
      "tags": "科幻",
      "comment": "两个人物被我玩趴还是最喜欢RK800"
    }
  ]
}
```

## 7. Key Notes

### Rating class mapping

| Category | Class pattern | Example | Stars |
|----------|--------------|---------|-------|
| Books/Movies | `rating{N}-t` | `rating5-t` | 5 |
| Games | `allstar{N}0` | `allstar50` | 5 |

### URL patterns

| Data | URL | Same page? |
|------|-----|-----------|
| Profile | `/people/{userId}/` | - |
| Notes | `/mine/notes` | Yes |
| Reviews | `/people/{userId}/reviews` | No (new tab) |
| Books | `book.douban.com/people/{userId}/collect` | No (new tab) |
| Movies | `movie.douban.com/people/{userId}/collect` | No (new tab) |
| Games | `/people/{userId}/games?action=collect` | No (new tab) |

### Pagination

- Reviews: `?start=10`, `?start=20` ... (10 per page, 146 total = 15 pages)
- Books: check for next page link
- Movies: check for next page link

### Anti-scraping

- Douban returns HTTP 418 for direct `urllib`/`requests` without proper headers
- Playwright CLI handles cookies/sessions automatically within a session
- Use `--persistent` flag to persist browser profile across restarts
- Saved state in `.playwright/douban-state.json` bypasses re-login
- Cookies have expiration; when expired, re-scan QR and re-save state
