from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx, os, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="API Gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SERVICES = {
    "auth":           os.getenv("AUTH_SERVICE_URL",           "http://auth-service:8001"),
    "orders":         os.getenv("ORDER_SERVICE_URL",          "http://order-service:8002"),
    "stock":          os.getenv("STOCK_SERVICE_URL",          "http://stock-service:8003"),
    "payments":       os.getenv("PAYMENT_SERVICE_URL",        "http://payment-service:8004"),
    "delivery":       os.getenv("DELIVERY_SERVICE_URL",       "http://delivery-service:8005"),
    "recommendations":os.getenv("RECOMMENDATION_SERVICE_URL", "http://recommendation-service:8006"),
}

@app.api_route("/{service}/{path:path}", methods=["GET","POST","PUT","DELETE","PATCH"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICES:
        raise HTTPException(404, f"Service '{service}' not found")
    target = f"{SERVICES[service]}/{path}"
    params = dict(request.query_params)
    body   = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host","content-length")}
    logger.info(f"→ {request.method} /{service}/{path}")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(request.method, target, params=params, content=body, headers=headers)
    from fastapi.responses import Response
    return Response(content=resp.content, status_code=resp.status_code,
                    media_type=resp.headers.get("content-type","application/json"))

@app.get("/health")
def health():
    return {"status": "gateway ok", "services": list(SERVICES.keys())}
