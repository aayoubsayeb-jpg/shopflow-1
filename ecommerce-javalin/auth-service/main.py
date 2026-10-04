from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import sqlite3, hashlib, jwt, os, datetime, pathlib

pathlib.Path("/app/data").mkdir(parents=True, exist_ok=True)
DB = "/app/data/auth.db"
SECRET = os.getenv("JWT_SECRET", "ecommerce_super_secret_2024")
ALGO   = "HS256"

app = FastAPI(title="Auth Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
security = HTTPBearer()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            email    TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            created  TEXT    DEFAULT (datetime('now'))
        )""")
        c.commit()

init_db()

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def make_token(user_id: int, username: str) -> str:
    payload = {"sub": user_id, "username": username,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)}
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except Exception:
        raise HTTPException(401, "Invalid token")

class RegisterReq(BaseModel):
    username: str
    email: str
    password: str

class LoginReq(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(req: RegisterReq):
    try:
        with get_db() as c:
            c.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",
                      (req.username, req.email, hash_pw(req.password)))
            c.commit()
            uid = c.execute("SELECT id FROM users WHERE username=?", (req.username,)).fetchone()["id"]
        return {"token": make_token(uid, req.username), "username": req.username, "user_id": uid}
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Username or email already exists")

@app.post("/login")
def login(req: LoginReq):
    with get_db() as c:
        user = c.execute("SELECT * FROM users WHERE username=? AND password=?",
                         (req.username, hash_pw(req.password))).fetchone()
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return {"token": make_token(user["id"], user["username"]),
            "username": user["username"], "user_id": user["id"]}

@app.get("/verify")
def verify(credentials: HTTPAuthorizationCredentials = Depends(security)):
    data = verify_token(credentials.credentials)
    return {"valid": True, "user_id": data["sub"], "username": data["username"]}

@app.get("/health")
def health():
    return {"status": "auth ok"}
