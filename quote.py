import requests, sqlite3, time
from bs4 import BeautifulSoup
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "quote.db")

def session():
    url = "https://quotes.toscrape.com/login"
    s = requests.Session()
    resp = s.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    csrf_tag = soup.find("input", {"type": "hidden", "name": "csrf_token"})
    if not csrf_tag:
        print("找不到csrf令牌！")
        return None
    data = {
        "csrf_token": csrf_tag["value"], 
        "username": "yibai",
        "password": "888888"
    }
    resp_post = s.post(url, data=data)
    if "Logout" not in resp_post.text:
        print("登陆失败！")
        return None
    
    return s

def get_page(s, url):
    try:
        resp = s.get(url, timeout=7)
        resp.raise_for_status()
    except Exception as e:
        print("请求失败:", e)
        return None

    return BeautifulSoup(resp.text, "html.parser")
    
def parse_page(soup):
    data = [] 
    for q in soup.find_all("div", class_="quote"):
        text = q.find("span", class_="text").get_text()
        author = q.find("small", class_="author").get_text()
        tags = [t.get_text() for t in q.find_all("a", class_="tag")]
        data.append((text, author, ",".join(tags)))
    return data

def conn_open():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
            CREATE TABLE IF NOT EXISTS quotes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT, author TEXT, tags TEXT)
            """)
    return cur, conn

def save(cur, data):
    for text, author, tags in data:
        cur.execute(
            "INSERT INTO quotes (text, author, tags) VALUES (?, ?, ?)",
            (text, author, tags)
        )

def conn_close(conn):
    conn.commit()
    conn.close()

def clear_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS quotes
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT, author TEXT, tags TEXT)
            """)
    cur.execute("DELETE FROM quotes")
    conn.commit()
    conn.close()

def main():
    clear_db()

    s = session()
    if not s:
        print("登陆失败！")
        return
    
    BASE = "https://quotes.toscrape.com"
    url = "/"
    start = time.time()
    print("查询数据中...")

    cur, conn = conn_open()
    while url:
        soup = get_page(s, BASE + url)
        if soup is None:
            break
        save(cur, parse_page(soup))
        next_tag = soup.find("li", class_="next")
        url = next_tag.find("a")["href"] if next_tag else None
        time.sleep(0.2)
    
    cur.execute("SELECT COUNT(*) FROM quotes")
    print("数据库里有", cur.fetchone()[0], "条")
    conn_close(conn)

    over = time.time()

    print("全部抓完...", f"共耗时{over-start:.2f}")

main()