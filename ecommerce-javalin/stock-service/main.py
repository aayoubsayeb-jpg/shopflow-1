from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3, pathlib, json

pathlib.Path("/app/data").mkdir(parents=True, exist_ok=True)
DB = "/app/data/stock.db"

app = FastAPI(title="Stock Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

PRODUCTS = [
    ("iPhone 15 Pro", "Electronics", 999.99, 50, "Latest Apple smartphone with titanium design, A17 Pro chip, and 48MP camera system.", "📱", ["smartphone","apple","mobile","camera","tech"]),
    ("Samsung Galaxy S24", "Electronics", 849.99, 40, "Android flagship with Galaxy AI, 200MP camera, and 7-year OS updates.", "📱", ["smartphone","samsung","android","camera","tech"]),
    ("MacBook Air M3", "Computers", 1299.99, 25, "Ultra-thin laptop with Apple M3 chip, 18-hour battery, and Liquid Retina display.", "💻", ["laptop","apple","computer","work","portable"]),
    ("Sony WH-1000XM5", "Audio", 349.99, 60, "Industry-leading noise canceling headphones with 30-hour battery life.", "🎧", ["headphones","audio","sony","music","noise-cancel"]),
    ("Nike Air Max 270", "Shoes", 129.99, 100, "Iconic Air Max cushioning with a large heel unit for all-day comfort.", "👟", ["shoes","nike","sport","running","casual"]),
    ("Adidas Ultraboost 23", "Shoes", 189.99, 80, "Energy-returning running shoes with Primeknit+ upper and Continental rubber sole.", "👟", ["shoes","adidas","running","sport","boost"]),
    ("iPad Pro 13-inch", "Electronics", 1099.99, 30, "Most powerful iPad with M4 chip, Ultra Retina XDR display, and Apple Pencil Pro support.", "📱", ["tablet","apple","ipad","work","creative"]),
    ("Dyson V15 Detect", "Home", 749.99, 20, "Laser reveals invisible dust, automatically adapts suction power to the surface.", "🏠", ["vacuum","dyson","home","cleaning","smart"]),
    ("Levi's 501 Jeans", "Clothing", 79.99, 150, "The original straight-fit jeans since 1873. Iconic 5-pocket styling in premium denim.", "👕", ["jeans","levis","clothing","fashion","casual"]),
    ("AirPods Pro 2nd Gen", "Audio", 249.99, 75, "Active Noise Cancellation, Transparency mode, Adaptive Audio with H2 chip.", "🎧", ["earbuds","apple","audio","wireless","music"]),
    ("Canon EOS R6 Mark II", "Cameras", 2499.99, 15, "Full-frame mirrorless camera with 40fps burst, 6K RAW video, and advanced AF.", "📷", ["camera","canon","photography","mirrorless","professional"]),
    ("The North Face Jacket", "Clothing", 299.99, 45, "DryVent waterproof shell jacket for all-season mountain performance.", "🧥", ["jacket","clothing","outdoor","winter","waterproof"]),
    ("Kindle Paperwhite", "Electronics", 139.99, 90, "300 ppi glare-free display, 3-month battery, and IPX8 waterproof rating.", "📚", ["ebook","kindle","amazon","reading","portable"]),
    ("Logitech MX Master 3S", "Computers", 99.99, 65, "Advanced wireless mouse with MagSpeed scroll, 8K DPI, and multi-device support.", "🖱️", ["mouse","logitech","computer","wireless","productivity"]),
    ("GoPro Hero 12 Black", "Cameras", 399.99, 35, "5.3K video, HyperSmooth 6.0 stabilization, and TimeWarp 3.0.", "📷", ["camera","gopro","action","sport","waterproof"]),
]

def init_db():
    with get_db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS products(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            category    TEXT NOT NULL,
            price       REAL NOT NULL,
            quantity    INTEGER NOT NULL,
            description TEXT,
            emoji       TEXT DEFAULT '📦',
            tags        TEXT DEFAULT '[]'
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS reservations(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            order_id   TEXT NOT NULL,
            quantity   INTEGER NOT NULL,
            created    TEXT DEFAULT (datetime('now'))
        )""")
        count = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            for p in PRODUCTS:
                c.execute("INSERT INTO products(name,category,price,quantity,description,emoji,tags) VALUES(?,?,?,?,?,?,?)",
                          (p[0],p[1],p[2],p[3],p[4],p[5],json.dumps(p[6])))
        c.commit()

init_db()

@app.get("/products")
def list_products(category: str = None, search: str = None):
    with get_db() as c:
        q = "SELECT * FROM products WHERE quantity > 0"
        params = []
        if category:
            q += " AND category=?"; params.append(category)
        if search:
            q += " AND (name LIKE ? OR description LIKE ?)"; params += [f"%{search}%", f"%{search}%"]
        rows = c.execute(q, params).fetchall()
    return [dict(r) for r in rows]

@app.get("/products/{pid}")
def get_product(pid: int):
    with get_db() as c:
        row = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not row: raise HTTPException(404, "Product not found")
    return dict(row)

@app.get("/categories")
def categories():
    with get_db() as c:
        rows = c.execute("SELECT DISTINCT category FROM products").fetchall()
    return [r["category"] for r in rows]

@app.post("/reserve")
def reserve(data: dict):
    pid, oid, qty = data["product_id"], data["order_id"], data["quantity"]
    with get_db() as c:
        p = c.execute("SELECT quantity FROM products WHERE id=?", (pid,)).fetchone()
        if not p or p["quantity"] < qty:
            raise HTTPException(400, "Insufficient stock")
        c.execute("UPDATE products SET quantity=quantity-? WHERE id=?", (qty, pid))
        c.execute("INSERT INTO reservations(product_id,order_id,quantity) VALUES(?,?,?)", (pid, oid, qty))
        c.commit()
    return {"status": "reserved", "product_id": pid, "quantity": qty}

@app.post("/release")
def release(data: dict):
    pid, oid = data["product_id"], data["order_id"]
    with get_db() as c:
        res = c.execute("SELECT quantity FROM reservations WHERE product_id=? AND order_id=?", (pid,oid)).fetchone()
        if res:
            c.execute("UPDATE products SET quantity=quantity+? WHERE id=?", (res["quantity"], pid))
            c.execute("DELETE FROM reservations WHERE product_id=? AND order_id=?", (pid, oid))
            c.commit()
    return {"status": "released"}

@app.get("/health")
def health():
    return {"status": "stock ok"}
