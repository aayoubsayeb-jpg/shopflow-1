from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, pathlib, httpx, uuid, os

pathlib.Path("/app/data").mkdir(parents=True, exist_ok=True)
DB = "/app/data/orders.db"

STOCK_URL    = os.getenv("STOCK_URL",    "http://stock-service:8003")
PAYMENT_URL  = os.getenv("PAYMENT_URL",  "http://payment-service:8004")
DELIVERY_URL = os.getenv("DELIVERY_URL", "http://delivery-service:8005")

app = FastAPI(title="Order Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init_db():
    with get_db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS orders(
            id          TEXT PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            product_id  INTEGER NOT NULL,
            product_name TEXT,
            quantity    INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status      TEXT DEFAULT 'PENDING',
            payment_id  TEXT,
            delivery_id TEXT,
            created     TEXT DEFAULT (datetime('now'))
        )""")
        c.commit()

init_db()

@app.post("/create")
def create_order(data: dict):
    order_id = str(uuid.uuid4())[:8].upper()
    with get_db() as c:
        c.execute("""INSERT INTO orders(id,user_id,product_id,product_name,quantity,total_price,status)
                     VALUES(?,?,?,?,?,?,?)""",
                  (order_id, data["user_id"], data["product_id"], data.get("product_name",""),
                   data["quantity"], data["total_price"], "PENDING"))
        c.commit()
    return {"order_id": order_id, "status": "PENDING"}

@app.post("/{order_id}/confirm-payment")
def confirm_payment(order_id: str, data: dict):
    with get_db() as c:
        o = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not o: raise HTTPException(404, "Order not found")
        c.execute("UPDATE orders SET status='PAID', payment_id=? WHERE id=?",
                  (data.get("payment_id",""), order_id))
        c.commit()
    # Reserve stock
    try:
        httpx.post(f"{STOCK_URL}/reserve",
                   json={"product_id": o["product_id"], "order_id": order_id, "quantity": o["quantity"]},
                   timeout=5)
    except: pass
    # Create delivery
    try:
        dr = httpx.post(f"{DELIVERY_URL}/create",
                        json={"order_id": order_id, "user_id": o["user_id"],
                              "product_name": o["product_name"]},
                        timeout=5)
        if dr.status_code == 200:
            did = dr.json().get("delivery_id")
            with get_db() as c:
                c.execute("UPDATE orders SET delivery_id=? WHERE id=?", (did, order_id))
                c.commit()
    except: pass
    return {"status": "PAID", "order_id": order_id}

@app.get("/user/{user_id}")
def user_orders(user_id: int):
    with get_db() as c:
        rows = c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created DESC", (user_id,)).fetchall()
    return [dict(r) for r in rows]

@app.get("/{order_id}")
def get_order(order_id: str):
    with get_db() as c:
        row = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not row: raise HTTPException(404, "Order not found")
    return dict(row)

@app.get("/health")
def health():
    return {"status": "orders ok"}
