from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, pathlib, json, numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

pathlib.Path("/app/data").mkdir(parents=True, exist_ok=True)
DB = "/app/data/recommendations.db"

app = FastAPI(title="Recommendation Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Product catalogue (same as stock) ───────────────────────────────────────
PRODUCTS = {
    1:  {"name":"iPhone 15 Pro",        "category":"Electronics","tags":"smartphone apple mobile camera tech",         "price":999.99,  "emoji":"📱"},
    2:  {"name":"Samsung Galaxy S24",   "category":"Electronics","tags":"smartphone samsung android camera tech",      "price":849.99,  "emoji":"📱"},
    3:  {"name":"MacBook Air M3",       "category":"Computers",  "tags":"laptop apple computer work portable",         "price":1299.99, "emoji":"💻"},
    4:  {"name":"Sony WH-1000XM5",      "category":"Audio",      "tags":"headphones audio sony music noise-cancel",    "price":349.99,  "emoji":"🎧"},
    5:  {"name":"Nike Air Max 270",     "category":"Shoes",      "tags":"shoes nike sport running casual",             "price":129.99,  "emoji":"👟"},
    6:  {"name":"Adidas Ultraboost 23", "category":"Shoes",      "tags":"shoes adidas running sport boost",            "price":189.99,  "emoji":"👟"},
    7:  {"name":"iPad Pro 13-inch",     "category":"Electronics","tags":"tablet apple ipad work creative",             "price":1099.99, "emoji":"📱"},
    8:  {"name":"Dyson V15 Detect",     "category":"Home",       "tags":"vacuum dyson home cleaning smart",            "price":749.99,  "emoji":"🏠"},
    9:  {"name":"Levi's 501 Jeans",     "category":"Clothing",   "tags":"jeans levis clothing fashion casual",         "price":79.99,   "emoji":"👕"},
    10: {"name":"AirPods Pro 2nd Gen",  "category":"Audio",      "tags":"earbuds apple audio wireless music",          "price":249.99,  "emoji":"🎧"},
    11: {"name":"Canon EOS R6 Mark II", "category":"Cameras",    "tags":"camera canon photography mirrorless professional","price":2499.99,"emoji":"📷"},
    12: {"name":"The North Face Jacket","category":"Clothing",   "tags":"jacket clothing outdoor winter waterproof",   "price":299.99,  "emoji":"🧥"},
    13: {"name":"Kindle Paperwhite",    "category":"Electronics","tags":"ebook kindle amazon reading portable",        "price":139.99,  "emoji":"📚"},
    14: {"name":"Logitech MX Master 3S","category":"Computers",  "tags":"mouse logitech computer wireless productivity","price":99.99,  "emoji":"🖱️"},
    15: {"name":"GoPro Hero 12 Black",  "category":"Cameras",    "tags":"camera gopro action sport waterproof",        "price":399.99,  "emoji":"📷"},
}

# ── TF-IDF content-based similarity matrix ──────────────────────────────────
def build_similarity_matrix():
    ids   = sorted(PRODUCTS.keys())
    corpus = [f"{PRODUCTS[i]['category']} {PRODUCTS[i]['tags']}" for i in ids]
    tfidf  = TfidfVectorizer(stop_words="english")
    matrix = tfidf.fit_transform(corpus)
    sim    = cosine_similarity(matrix)
    return {ids[i]: {ids[j]: float(sim[i][j]) for j in range(len(ids))} for i in range(len(ids))}

SIM_MATRIX = build_similarity_matrix()

# ── Collaborative filtering helpers ─────────────────────────────────────────
def get_db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init_db():
    with get_db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS purchases(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            created    TEXT DEFAULT (datetime('now'))
        )""")
        c.commit()

init_db()

def content_based_recs(product_id: int, top_n: int = 5, exclude: list = []) -> list:
    """Return top-N similar products using TF-IDF cosine similarity"""
    if product_id not in SIM_MATRIX:
        return []
    scores = SIM_MATRIX[product_id]
    ranked = sorted([(pid, score) for pid, score in scores.items()
                     if pid != product_id and pid not in exclude],
                    key=lambda x: x[1], reverse=True)
    result = []
    for pid, score in ranked[:top_n]:
        p = dict(PRODUCTS[pid])
        p["product_id"] = pid
        p["similarity_score"] = round(score, 3)
        p["reason"] = _reason(product_id, pid)
        result.append(p)
    return result

def collaborative_recs(user_id: int, top_n: int = 5) -> list:
    """Simple user-based CF: find users who bought same items, recommend theirs"""
    with get_db() as c:
        my_purchases = [r["product_id"] for r in
                        c.execute("SELECT product_id FROM purchases WHERE user_id=?", (user_id,)).fetchall()]
        if not my_purchases:
            return []
        # Users who share at least one product
        similar_users = [r["user_id"] for r in c.execute(
            f"SELECT DISTINCT user_id FROM purchases WHERE product_id IN ({','.join('?'*len(my_purchases))}) AND user_id!=?",
            (*my_purchases, user_id)).fetchall()]
        if not similar_users:
            return []
        # Products those users bought that I haven't
        their_products = [r["product_id"] for r in c.execute(
            f"SELECT product_id, COUNT(*) as cnt FROM purchases WHERE user_id IN ({','.join('?'*len(similar_users))}) "
            f"AND product_id NOT IN ({','.join('?'*len(my_purchases))}) GROUP BY product_id ORDER BY cnt DESC LIMIT ?",
            (*similar_users, *my_purchases, top_n)).fetchall()]
    result = []
    for pid in their_products:
        if pid in PRODUCTS:
            p = dict(PRODUCTS[pid])
            p["product_id"] = pid
            p["reason"] = "🤝 ما اشتراه عملاء مشابهون لك"
            result.append(p)
    return result

def _reason(source_id: int, target_id: int) -> str:
    s = PRODUCTS.get(source_id, {}); t = PRODUCTS.get(target_id, {})
    if s.get("category") == t.get("category"):
        return f"🏷️ نفس الفئة: {t['category']}"
    s_tags = set(s.get("tags","").split())
    t_tags = set(t.get("tags","").split())
    common = s_tags & t_tags
    if common:
        return f"🔗 خصائص مشتركة: {', '.join(list(common)[:2])}"
    return "⭐ منتج مقترح"

@app.post("/record-purchase")
def record_purchase(data: dict):
    with get_db() as c:
        c.execute("INSERT INTO purchases(user_id,product_id) VALUES(?,?)",
                  (data["user_id"], data["product_id"]))
        c.commit()
    return {"status": "recorded"}

@app.get("/for-product/{product_id}")
def for_product(product_id: int, user_id: int = None):
    """Hybrid: content-based + collaborative"""
    cb = content_based_recs(product_id, top_n=4)
    cf = []
    if user_id:
        cf = collaborative_recs(user_id, top_n=2)
        seen_ids = {r["product_id"] for r in cb}
        cf = [r for r in cf if r["product_id"] not in seen_ids]
    result = cb + cf
    return {"recommendations": result[:6], "method": "hybrid_ml",
            "based_on": PRODUCTS.get(product_id, {}).get("name","Unknown")}

@app.get("/for-user/{user_id}")
def for_user(user_id: int):
    cf = collaborative_recs(user_id, top_n=6)
    if not cf:
        # Cold start: return popular / diverse items
        import random
        pids = random.sample(list(PRODUCTS.keys()), min(6, len(PRODUCTS)))
        cf = [dict(PRODUCTS[p], product_id=p, reason="⭐ منتجات مقترحة لك") for p in pids]
    return {"recommendations": cf, "method": "collaborative_filtering"}

@app.get("/health")
def health():
    return {"status": "recommendation ok", "model": "TF-IDF + Collaborative Filtering"}
