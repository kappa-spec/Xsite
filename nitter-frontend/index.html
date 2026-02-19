from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import feedparser
import re
from urllib.parse import quote

app = FastAPI()

# CORS設定（VercelのURLが確定したら"*"を書き換えると安全です）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 比較的安定しているパブリックインスタンス
NITTER_INSTANCE = "https://nitter.net"

def clean_summary(html_content):
    # 画像URLの抽出
    images = re.findall(r'<img src="([^"]+)"', html_content)
    images = [img if img.startswith("http") else f"{NITTER_INSTANCE}{img}" for img in images]
    # HTMLタグ除去とテキスト整形
    text = re.sub(r'<[^>]+>', '', html_content)
    return text, images

@app.get("/api/search")
async def search(q: str = Query(...)):
    # @から始まればユーザーRSS、それ以外は検索RSS
    is_user = q.startswith('@')
    path = f"/{q[1:]}/rss" if is_user else f"/search/rss?q={quote(q)}"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            r = await client.get(f"{NITTER_INSTANCE}{path}", timeout=15.0)
            if r.status_code != 200: raise HTTPException(status_code=404)
            
            feed = feedparser.parse(r.text)
            # ユーザープロフ画像（検索時は空になる場合がある）
            p_img = feed.feed.image.url.replace("http://", "https://") if 'image' in feed.feed else ""
            
            results = []
            for e in feed.entries:
                text, imgs = clean_summary(e.summary)
                results.append({
                    "author": e.get('author', q),
                    "handle": q if is_user else e.get('author', ''),
                    "text": text,
                    "imgs": imgs,
                    "date": e.published,
                    "link": e.link
                })
            return {"title": feed.feed.title, "p_img": p_img, "tweets": results}
        except:
            raise HTTPException(status_code=500, detail="Instance Error")
