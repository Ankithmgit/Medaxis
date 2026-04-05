from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx, os, sys, json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.auth_utils import get_current_user

app = FastAPI(title="MedAxis AI Service", version="1.0.0",
              description="Agentic AI: alerts, recommendations, conversational querying")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

INVENTORY_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8002")
BILLING_URL   = os.getenv("BILLING_SERVICE_URL",   "http://localhost:8003")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Guardrails ───────────────────────────────────────────────
BLOCKED_TOPICS = ["dosage advice", "medical diagnosis", "prescribe", "treatment", "cure", "drug interaction"]

def check_guardrails(query: str) -> Optional[str]:
    q_lower = query.lower()
    for topic in BLOCKED_TOPICS:
        if topic in q_lower:
            return f"I can't provide medical/clinical advice ('{topic}'). Please consult a licensed pharmacist or physician."
    return None

# ── Helpers: fetch from other services ──────────────────────
async def fetch_low_stock(store_id: Optional[int], token: str):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"store_id": store_id} if store_id else {}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{INVENTORY_URL}/stock/low-stock", params=params, headers=headers, timeout=5)
    return r.json() if r.status_code == 200 else []

async def fetch_expiring_soon(days: int, store_id: Optional[int], token: str):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"days": days}
    if store_id:
        params["store_id"] = store_id
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{INVENTORY_URL}/batches/expiring-soon", params=params, headers=headers, timeout=5)
    return r.json() if r.status_code == 200 else []

async def fetch_daily_summary(store_id: Optional[int], token: str):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"store_id": store_id} if store_id else {}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BILLING_URL}/billing/summary/daily", params=params, headers=headers, timeout=5)
    return r.json() if r.status_code == 200 else []

# ── Endpoints ────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"service": "ai-service", "status": "ok"}

@app.get("/ai/alerts")
async def get_all_alerts(store_id: int = Query(None), current_user=Depends(get_current_user),
                         token: str = Depends(lambda req: req.headers.get("authorization", "").replace("Bearer ", ""))):
    """Aggregate low-stock and near-expiry alerts with AI-generated recommendations."""
    low_stock = await fetch_low_stock(store_id, token)
    expiring = await fetch_expiring_soon(30, store_id, token)

    alerts = []

    for item in low_stock:
        alerts.append({
            "type": "LOW_STOCK",
            "severity": "HIGH" if item["current_stock"] == 0 else "MEDIUM",
            "product": item["product_name"],
            "sku": item["sku"],
            "current_stock": item["current_stock"],
            "reorder_level": item["reorder_level"],
            "recommendation": f"Reorder at least {item['deficit'] * 2} units of {item['product_name']} to cover 2x deficit.",
        })

    for b in expiring:
        days_left = b["days_until_expiry"]
        severity = "CRITICAL" if days_left <= 7 else "HIGH" if days_left <= 15 else "MEDIUM"
        alerts.append({
            "type": "EXPIRY_ALERT",
            "severity": severity,
            "product": b["product_name"],
            "sku": b["sku"],
            "batch_number": b["batch_number"],
            "quantity": b["quantity"],
            "expiry_date": b["expiry_date"],
            "days_until_expiry": days_left,
            "recommendation": (
                f"Only {days_left} days left. Consider markdowns, inter-store transfer, or return to distributor."
                if days_left > 0 else "EXPIRED — remove from shelf immediately."
            ),
        })

    return {
        "total_alerts": len(alerts),
        "store_id": store_id,
        "alerts": sorted(alerts, key=lambda x: ["CRITICAL","HIGH","MEDIUM"].index(x["severity"]))
    }

@app.get("/ai/demand-forecast")
async def demand_forecast(store_id: int = Query(None), current_user=Depends(get_current_user),
                          token: str = Depends(lambda req: req.headers.get("authorization", "").replace("Bearer ", ""))):
    """Simple demand forecast hint based on recent sales trends."""
    summary = await fetch_daily_summary(store_id, token)
    if not summary:
        return {"message": "Not enough sales data for forecasting."}

    revenues = [row["total_revenue"] or 0 for row in summary[:7]]
    avg_daily = sum(revenues) / len(revenues) if revenues else 0
    trend = "growing" if len(revenues) >= 2 and revenues[0] > revenues[-1] else "stable or declining"

    return {
        "store_id": store_id,
        "avg_daily_revenue_last_7_days": round(avg_daily, 2),
        "trend": trend,
        "forecast_next_7_days_revenue": round(avg_daily * 7 * (1.05 if trend == "growing" else 1.0), 2),
        "insight": f"Revenue trend is {trend}. {'Consider stocking fast-moving OTC items.' if trend == 'growing' else 'Review slow-moving inventory and reduce wastage.'}",
        "disclaimer": "This is a heuristic estimate only. Consult your regional manager for procurement decisions.",
    }

# ── Conversational Query (Claude API) ───────────────────────
class QueryRequest(BaseModel):
    question: str
    store_id: Optional[int] = None

@app.post("/ai/query")
async def conversational_query(req: QueryRequest, current_user=Depends(get_current_user),
                                token: str = Depends(lambda r: r.headers.get("authorization","").replace("Bearer ",""))):
    """Natural language querying of pharmacy operations data."""

    # Guardrail check first
    blocked = check_guardrails(req.question)
    if blocked:
        return {"answer": blocked, "guardrail_triggered": True}

    if not ANTHROPIC_API_KEY:
        return {"answer": "AI querying is not configured. Set ANTHROPIC_API_KEY to enable this feature.", "guardrail_triggered": False}

    # Fetch context data to pass to Claude
    low_stock = await fetch_low_stock(req.store_id, token)
    expiring = await fetch_expiring_soon(30, req.store_id, token)
    sales = await fetch_daily_summary(req.store_id, token)

    context = f"""
You are a pharmacy operations assistant for MedAxis Health Retail.
You ONLY answer questions about inventory, stock, sales, expiry, and operations.
You do NOT give medical advice, drug dosage recommendations, or clinical guidance.

Current Data Context:
- Low stock items: {json.dumps(low_stock[:10])}
- Expiring soon (30 days): {json.dumps(expiring[:10])}
- Recent daily sales: {json.dumps(sales[:7])}

Store filter: {req.store_id or 'All stores'}

Answer the user's question using only the data above. Be concise and actionable.
If the question is outside pharmacy operations scope, politely decline.
"""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 512,
                "system": context,
                "messages": [{"role": "user", "content": req.question}]
            },
            timeout=15.0
        )

    if resp.status_code != 200:
        raise HTTPException(502, "AI service error. Please try again.")

    data = resp.json()
    answer = data["content"][0]["text"] if data.get("content") else "No response from AI."
    return {"answer": answer, "guardrail_triggered": False}
