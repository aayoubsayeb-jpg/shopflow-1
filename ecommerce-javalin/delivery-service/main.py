from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, pathlib, uuid, math, random, time
from datetime import datetime

pathlib.Path("/app/data").mkdir(parents=True, exist_ok=True)
DB = "/app/data/delivery.db"

app = FastAPI(title="Delivery Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Warehouse location (Algiers)
WAREHOUSE = {"lat": 36.7372, "lng": 3.0866, "name": "Entrepôt Central - Alger"}

# Destination zones (random city areas)
DESTINATIONS = [
    {"lat": 36.7525, "lng": 3.0420, "name": "Bab El Oued"},
    {"lat": 36.7762, "lng": 3.0585, "name": "El Mouradia"},
    {"lat": 36.7188, "lng": 3.1413, "name": "Hussein Dey"},
    {"lat": 36.7300, "lng": 2.9800, "name": "Bir Mourad Raïs"},
    {"lat": 36.8000, "lng": 3.0600, "name": "El Biar"},
    {"lat": 36.7650, "lng": 3.0950, "name": "Belouizdad"},
    {"lat": 36.7100, "lng": 3.1600, "name": "Kouba"},
    {"lat": 36.7900, "lng": 2.9500, "name": "Chéraga"},
]

STATUSES = ["WAREHOUSE", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"]
STATUS_LABELS = {
    "WAREHOUSE":         "📦 في المستودع",
    "PICKED_UP":         "🚛 تم الاستلام",
    "IN_TRANSIT":        "🚚 في الطريق",
    "OUT_FOR_DELIVERY":  "🏃 خارج للتوصيل",
    "DELIVERED":         "✅ تم التوصيل",
}

def get_db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init_db():
    with get_db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS deliveries(
            id             TEXT PRIMARY KEY,
            order_id       TEXT UNIQUE NOT NULL,
            user_id        INTEGER NOT NULL,
            product_name   TEXT,
            tracking_number TEXT UNIQUE NOT NULL,
            status         TEXT DEFAULT 'WAREHOUSE',
            current_lat    REAL,
            current_lng    REAL,
            dest_lat       REAL,
            dest_lng       REAL,
            dest_name      TEXT,
            warehouse_lat  REAL DEFAULT 36.7372,
            warehouse_lng  REAL DEFAULT 3.0866,
            progress       REAL DEFAULT 0.0,
            last_updated   TEXT DEFAULT (datetime('now')),
            created        TEXT DEFAULT (datetime('now'))
        )""")
        c.commit()

init_db()

def interpolate(lat1, lng1, lat2, lng2, t):
    """Linear interpolation between two points"""
    return lat1 + (lat2 - lat1) * t, lng1 + (lng2 - lng1) * t

def get_status_from_progress(progress: float) -> str:
    if progress < 0.05:   return "WAREHOUSE"
    if progress < 0.20:   return "PICKED_UP"
    if progress < 0.75:   return "IN_TRANSIT"
    if progress < 0.95:   return "OUT_FOR_DELIVERY"
    return "DELIVERED"

def update_position(delivery_id: str):
    """Advance delivery progress based on time elapsed"""
    with get_db() as c:
        d = c.execute("SELECT * FROM deliveries WHERE id=?", (delivery_id,)).fetchone()
        if not d or d["status"] == "DELIVERED":
            return
        # Progress increases ~2% per minute (full delivery in ~50 min)
        last = datetime.fromisoformat(d["last_updated"])
        elapsed_minutes = (datetime.utcnow() - last).total_seconds() / 60.0
        new_progress = min(1.0, d["progress"] + elapsed_minutes * 0.02)
        new_progress += random.uniform(-0.002, 0.005)  # small jitter
        new_progress = max(d["progress"], min(1.0, new_progress))

        lat, lng = interpolate(
            d["warehouse_lat"], d["warehouse_lng"],
            d["dest_lat"], d["dest_lng"], new_progress
        )
        # Add small GPS noise
        lat += random.uniform(-0.001, 0.001)
        lng += random.uniform(-0.001, 0.001)

        new_status = get_status_from_progress(new_progress)
        c.execute("""UPDATE deliveries SET current_lat=?, current_lng=?, progress=?,
                     status=?, last_updated=datetime('now') WHERE id=?""",
                  (lat, lng, new_progress, new_status, delivery_id))
        c.commit()

@app.post("/create")
def create_delivery(data: dict):
    delivery_id   = str(uuid.uuid4())
    tracking_num  = "TRK-" + str(uuid.uuid4())[:8].upper()
    dest          = random.choice(DESTINATIONS)
    with get_db() as c:
        c.execute("""INSERT INTO deliveries(id,order_id,user_id,product_name,tracking_number,
                     current_lat,current_lng,dest_lat,dest_lng,dest_name,progress)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (delivery_id, data["order_id"], data["user_id"],
                   data.get("product_name",""), tracking_num,
                   WAREHOUSE["lat"], WAREHOUSE["lng"],
                   dest["lat"], dest["lng"], dest["name"], 0.0))
        c.commit()
    return {"delivery_id": delivery_id, "tracking_number": tracking_num,
            "destination": dest["name"], "status": "WAREHOUSE"}

@app.get("/track/{tracking_number}")
def track(tracking_number: str):
    with get_db() as c:
        d = c.execute("SELECT * FROM deliveries WHERE tracking_number=?",
                      (tracking_number,)).fetchone()
    if not d: raise HTTPException(404, "Tracking number not found")
    update_position(d["id"])
    with get_db() as c:
        d = c.execute("SELECT * FROM deliveries WHERE tracking_number=?",
                      (tracking_number,)).fetchone()
    dd = dict(d)
    dd["status_label"] = STATUS_LABELS.get(dd["status"], dd["status"])
    dd["progress_pct"] = round(dd["progress"] * 100, 1)
    dd["warehouse"] = WAREHOUSE
    dd["eta_minutes"] = max(0, round((1.0 - dd["progress"]) * 50))
    return dd

@app.get("/order/{order_id}")
def by_order(order_id: str):
    with get_db() as c:
        d = c.execute("SELECT * FROM deliveries WHERE order_id=?", (order_id,)).fetchone()
    if not d: raise HTTPException(404, "Delivery not found for order")
    update_position(d["id"])
    with get_db() as c:
        d = c.execute("SELECT * FROM deliveries WHERE order_id=?", (order_id,)).fetchone()
    dd = dict(d)
    dd["status_label"] = STATUS_LABELS.get(dd["status"], dd["status"])
    dd["progress_pct"] = round(dd["progress"] * 100, 1)
    dd["eta_minutes"] = max(0, round((1.0 - dd["progress"]) * 50))
    return dd

@app.get("/health")
def health():
    return {"status": "delivery ok"}
