# ShopZone — منصة تجارة إلكترونية متكاملة

## structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend :8501                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  API Gateway :8000                           │
└──┬──────┬──────┬──────┬──────┬──────────────────────────────┘
   │      │      │      │      │
  Auth  Orders Stock Payment Delivery  Recommendations
 :8001  :8002  :8003  :8004   :8005       :8006
 Python Python Python  Java  Python      Python
 SQLite SQLite SQLite SQLite  SQLite      SQLite
                Spring Boot  GPS/Maps  ML TF-IDF+CF
```

## how to execute

```bash
#docker initialization
docker --version
docker-compose --version

#file destination
cd ecommerce


docker-compose up --build

#interface
# http://localhost:8501
```

## services

| service| port   |framework | DB  |
|--------|--------|---------|----------------|
| Frontend | 8501 | Streamlit | — |
| API Gateway | 8000 | FastAPI | — |
| Auth Service | 8001 | FastAPI + PyJWT | SQLite |
| Order Service | 8002 | FastAPI | SQLite |
| Stock Service | 8003 | FastAPI | SQLite |
| Payment Service | 8004 | Java Spring Boot | SQLite |
| Delivery Service | 8005 | FastAPI + GPS | SQLite |
| Recommendation | 8006 | FastAPI + sklearn | SQLite |

## catre must be 


```
card number:  4532 0151 1283 0366
expiration date : 12/26
CVV: 123
```

##  how to stop the execution

```bash
docker-compose down
# لحذف البيانات أيضاً
docker-compose down -v
```
