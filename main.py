import redis
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import SpotifyTrack
import csv_loader  # 启动时导入
from decimal import Decimal

# ==================== Database Table Creation and Data Import (First Run Only) ====================
# Note: The following two lines of code will recreate tables and re-import CSV data
# every time the service starts, which will result in data loss if data already exists.
# Therefore, it is recommended to comment them out in production or development
# and instead manually execute reset_database.py and csv_loader.py to manage data.

# SpotifyTrack.metadata.create_all(bind=engine)   # Optional: Enable only for initial deployment
# csv_loader.load_csv()                           # Optional: Enable only for initial deployment

# Tip: To initialize the database, execute the following in order:
#   1. python reset_database.py   (Recreate table schema)
#   2. python csv_loader.py       (Import cleaned data)

# --- FastAPI initilization ---
app = FastAPI(title="Spotify Analysis")
templates = Jinja2Templates(directory="templates")
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# --- Request Model ---
class SQLQuery(BaseModel):
    sql: str

# --- Page Routing ---
@app.get("/", response_class=HTMLResponse)

def Analysis(request: Request):
    return templates.TemplateResponse("Analysis.html", {"request": request})

# --- API Routes: Dynamic SQL Execution (with Caching and Validation) ---
@app.post("/api/query/execute")
def execute_query(query: SQLQuery):
    sql = query.sql.strip()
    
    # 1. Security validation (logic consistent with the Java version)
    # Reason: Even if you write only safe SQL on the frontend, external attackers can still call this 
    # API directly and send arbitrary SQL (such as DROP TABLE). Therefore, the server must validate all input.
    # Note: Modified to support WITH (CTE) queries, as CTEs are also read-only.
    lower_sql = sql.lower()
    if not lower_sql.startswith(("select", "with")):
        raise HTTPException(status_code=400, detail="Only SELECT or WITH queries are allowed.")
    if "spotify_tracks" not in lower_sql:
        raise HTTPException(status_code=400, detail="Only queries to the spotify_tracks table are allowed.")
    forbidden = ["drop", "truncate", "update", "delete", "alter", "insert"]
    for word in forbidden:
        if word in lower_sql:
            raise HTTPException(status_code=400, detail=f"SQL contains dangerous operations: {word}")
    
    # 2. Redis cache (using SQL statements as keys)
    cache_key = f"query:{hash(sql)}" # Use the hash value of the SQL statement as the key
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    
    # 3. Execute query
    db = SessionLocal()
    try:
        # Execute raw SQL (security checks have already been passed at this stage)
        result = db.execute(text(sql))
        columns = result.keys()
        rows = []
        # Convert Decimal type to float (for easier JSON serialization)
        for row in result.fetchall():
            converted_row = []
            for value in row:
                if isinstance(value, Decimal):
                    converted_row.append(float(value))
                else:
                    converted_row.append(value)
            rows.append(converted_row)

        
        response = {"columns": list(columns), "rows": rows}
        
        # 4. Store in Redis (cache for 5 minutes to prevent memory exhaustion)
        import json
        redis_client.setex(cache_key, 300, json.dumps(response))
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close() # Release database connection

# 启动命令（开发用）：
# uvicorn main:app --reload --host 0.0.0.0 --port 8080