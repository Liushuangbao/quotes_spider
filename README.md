# quote-spider

登录态爬虫：模拟登录 quotes.toscrape.com，抓取全站 100 条名言，存进 SQLite。

Python 3 + requests + BeautifulSoup4 + SQLite。

## 核心流程

```
1. requests.Session() 开启会话（自动管理 Cookie）
2. GET  /login      → 从返回的 HTML 里提取 csrf_token
3. POST /login      → 携带 csrf_token + 账号密码提交
4. 检查响应中含 "Logout"，确认登录成功
5. 从首页开始，靠 li.next 翻页，直到没有下一页
6. 每页解析出 (名言, 作者, 标签)，写入 SQLite
```

## 运行

```bash
pip install requests beautifulsoup4
python quote.py
```

跑完会在同目录生成 `quote.db`：

```
数据库里有 100 条
全部抓完... 共耗时 18.58
```

## 代码结构

```
session()             登录并返回带 Cookie 的 Session
get_page(s, url)      请求页面，返回 BeautifulSoup；失败返回 None
parse_page(soup)      拆出 [(名言, 作者, 标签), ...]
conn_open()           建库建表，返回 (cursor, connection)
save(cur, data)       批量写入
conn_close(conn)      统一 commit + close
clear_db()            每次运行前清空旧数据
main()                登录 → 翻页 → 解析 → 入库
```

## 表结构

```sql
CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    author TEXT,
    tags TEXT
);
```

## 几个有意的写法

- **登录态验证**：POST 后检查响应里有 `Logout` 才继续，避免带着未登录的 Session 爬一晚上
- **翻页**：读页面底部的 `li.next`，读不到就说明是最后一页——不用状态码判断（部分页面返回 200 但没有数据）
- **失败处理**：请求带 `timeout` + `raise_for_status()`，失败返回 None 并退出循环
- **单次连接**：整个程序只 `conn_open()` 一次，最后统一 commit——避免多个连接导致未提交事务丢失
- **写库用 `?` 占位符**：不拼字符串，避免 SQL 注入
- **每页之间 sleep 一下**：不给对方服务器添麻烦

## 数据样式

```
(text, author, tags)
"The world as we have created it is a process of our thinking..." | Albert Einstein | change,deep-thoughts,thinking,world
"It is our choices, Harry, that show what we truly are..."        | J.K. Rowling    | abilities,choices
```

注：全站有 3 条名言本身没有标签，入库时 tags 为空字符串，属于源站数据特征而非爬虫缺陷。
