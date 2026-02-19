from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import feedparser
import re
from urllib.parse import quote
from fastapi.responses import HTMLResponse

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

@app.get("/api/search", response_class=HTMLResponse)
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
            
            # 取得データをHTMLに流し込む
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ja">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{feed.feed.title}</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body {{ background-color: #000; color: #e7e9ea; font-family: sans-serif; }}
                    .x-border {{ border-color: #2f3336; }}
                    .i-search {{ width: 18px; height: 18px; border: 2px solid #71767b; border-radius: 50%; position: relative; }}
                    .i-search::after {{ content: ""; position: absolute; width: 2px; height: 7px; background: #71767b; bottom: -5px; right: -3px; transform: rotate(-45deg); }}
                    .i-msg {{ width: 18px; height: 14px; border: 2px solid #71767b; border-radius: 3px; position: relative; }}
                    .i-re {{ width: 18px; height: 10px; border-top: 2px solid #71767b; border-bottom: 2px solid #71767b; position: relative; }}
                    .i-heart {{ width: 12px; height: 12px; background: #71767b; transform: rotate(-45deg); position: relative; }}
                    .i-heart::before, .i-heart::after {{ content: ""; width: 12px; height: 12px; background: #71767b; border-radius: 50%; position: absolute; }}
                    .i-heart::before {{ top: -6px; left: 0; }} .i-heart::after {{ left: 6px; top: 0; }}
                </style>
            </head>
            <body class="flex justify-center">
                <main class="w-full max-w-[600px] min-h-screen border-x x-border">
                    <div class="sticky top-0 bg-black/80 backdrop-blur-md z-40 border-b x-border p-4">
                        <form action="/api/search" method="get" class="relative flex items-center">
                            <div class="absolute left-4 i-search"></div>
                            <input type="text" name="q" value="{q}" class="w-full bg-[#202327] rounded-full py-2.5 pl-12 pr-4 outline-none border border-transparent focus:border-[#1d9bf0] focus:bg-black transition" placeholder="Search">
                        </form>
                    </div>
                    
                    <div class="p-4 border-b x-border">
                        <div class="flex items-center space-x-4">
                            {"<img src='" + p_img + "' class='w-20 h-20 rounded-full border-4 border-black bg-gray-800'>" if p_img else "<div class='w-20 h-20 rounded-full bg-gray-700'></div>"}
                            <div>
                                <h1 class="text-xl font-bold">{feed.feed.title}</h1>
                                <p class="text-[#71767b]">{q}</p>
                            </div>
                        </div>
                    </div>

                    <div>
                        {"".join([f'''
                        <article class="p-4 border-b x-border hover:bg-white/[0.02] transition">
                            <div class="flex space-x-3">
                                <div class="w-10 h-10 rounded-full bg-gray-700 flex-shrink-0 flex items-center justify-center font-bold text-xs">
                                    {t['author'][0]}
                                </div>
                                <div class="flex-1">
                                    <div class="flex items-center space-x-1">
                                        <span class="font-bold text-[15px]">{t['author']}</span>
                                        <span class="text-[#71767b] text-[15px]">· {t['date']}</span>
                                    </div>
                                    <div class="text-[15px] leading-normal mt-0.5">{t['text']}</div>
                                    {"".join([f'<img src="{img}" class="mt-3 rounded-2xl border x-border w-full max-h-[512px] object-cover">' for img in t['imgs']])}
                                    <div class="flex justify-between mt-3 max-w-[425px] text-[#71767b]">
                                        <div class="flex items-center space-x-2"><div class="i-msg"></div><span class="text-xs">--</span></div>
                                        <div class="flex items-center space-x-2"><div class="i-re"></div><span class="text-xs">--</span></div>
                                        <div class="flex items-center space-x-2"><div class="i-heart"></div><span class="text-xs">--</span></div>
                                    </div>
                                </div>
                            </div>
                        </article>
                        ''' for t in results])}
                    </div>
                </main>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        except:
            raise HTTPException(status_code=500, detail="Instance Error")
