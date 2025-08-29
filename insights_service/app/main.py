# insights_service/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, timedelta
import os, requests, logging

# Vertex AI client (Gemini) imports
try:
    from vertexai import init
    from vertexai.preview.language_models import TextGenerationModel
    VERTEX_AVAILABLE = True
except Exception:
    VERTEX_AVAILABLE = False

app = FastAPI(title="Insights Service")
logging.basicConfig(level=logging.INFO)

BOA_BASE_URL = os.getenv("BOA_BASE_URL", "http://boa-gateway")
PROJECT_ID = os.getenv("GCP_PROJECT")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "text-bison@001")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "900"))  # basic caching placeholder

class InsightsResponse(BaseModel):
    user_id: str
    period: dict
    summary: dict
    categories: list
    merchants_top: list
    credit_utilization: dict
    narrative: str

# Simple in-memory cache (per-pod). For demo only.
cache = {}

def fetch_user_data(user_id: str):
    """Fetch user, accounts and transactions. Wraps Bank of Anthos endpoints.
    If your BoA gateway exposes different paths, update these URLs accordingly.
    """
    user_r = requests.get(f"{BOA_BASE_URL}/users/{user_id}", timeout=5)
    user_r.raise_for_status()
    user = user_r.json()

    accts_r = requests.get(f"{BOA_BASE_URL}/accounts/{user_id}", timeout=5)
    accts_r.raise_for_status()
    accts = accts_r.json()

    since = (date.today() - timedelta(days=30)).isoformat()
    txns = []
    for a in accts.get("accounts", []):
        aid = a.get("id")
        t = requests.get(f"{BOA_BASE_URL}/transactions?account_id={aid}&from={since}", timeout=10)
        t.raise_for_status()
        txns.extend(t.json().get("transactions", []))

    return user, accts, txns


def engineer_features(accts, txns):
    income = sum(t['amount'] for t in txns if t.get('type') == 'CREDIT')
    spend = sum(-t['amount'] for t in txns if t.get('type') == 'DEBIT')
    net = income - spend

    cats = {}
    merchants = {}
    for t in txns:
        merchant = (t.get('merchant') or 'Unknown').title()
        amt = abs(t.get('amount', 0))
        merchants[merchant] = merchants.get(merchant, 0) + amt
        m = merchant.lower()
        # heuristic categories (extendable)
        if any(k in m for k in ['coffee', 'cafe', 'restaurant', 'burger', 'pizza']):
            cat = 'Dining'
        elif any(k in m for k in ['market', 'grocery', 'foods']):
            cat = 'Groceries'
        elif any(k in m for k in ['uber', 'lyft', 'gas', 'transit']):
            cat = 'Transport'
        elif any(k in m for k in ['rent', 'mortgage']):
            cat = 'Housing'
        else:
            cat = 'Other'
        cats[cat] = cats.get(cat, 0) + amt

    top_merchants = sorted([{ 'name': k, 'sum': round(v, 2)} for k, v in merchants.items()], key=lambda x: x['sum'], reverse=True)[:5]

    limit = sum(a.get('credit_limit', 0) for a in accts.get('accounts', []))
    balance = sum(a.get('balance', 0) for a in accts.get('accounts', []))
    ratio = round((balance / limit) if limit else 0.0, 2)

    return {
        'summary': {'income': round(income,2), 'spend': round(spend,2), 'net': round(net,2)},
        'categories': [{'name': k, 'sum': round(v,2)} for k,v in cats.items()],
        'merchants_top': top_merchants,
        'credit_utilization': {'ratio': ratio, 'limit': limit, 'balance': balance}
    }


def gemini_narrative_safe(features: dict, user: dict) -> str:
    """Generate a concise narrative with Vertex AI (Gemini). If Vertex is unavailable, return a deterministic fallback."""
    prompt = (
        f"You are a helpful banking assistant. Given the monthly summary: {features['summary']} ";
        f"Top categories: {features['categories']}. Credit utilization: {features['credit_utilization']}"
        "Write 3 short sentences: one observation, one actionable tip, one caution (if utilization > 0.3). No PII. Keep under 100 words."
    )

    if VERTEX_AVAILABLE:
        try:
            init(project=PROJECT_ID, location=LOCATION)
            model = TextGenerationModel.from_pretrained(GEMINI_MODEL)
            response = model.predict(prompt, max_output_tokens=256)
            # TextGenerationModel.predict returns a generated text string
            return response.text.strip() if hasattr(response, 'text') else str(response)
        except Exception as e:
            logging.exception('Vertex call failed')
            # fallthrough to fallback

    # deterministic fallback narrative (explainable)
    s = features['summary']
    top_cat = max(features['categories'], key=lambda c: c['sum']) if features['categories'] else {'name':'N/A','sum':0}
    narrative = (
        f"In the last 30 days you had ${s['spend']} in spending and ${s['income']} in credits. "
        f"Your biggest category was {top_cat['name']} (${top_cat['sum']}). "
    )
    if features['credit_utilization']['ratio'] > 0.3:
        narrative += "Your credit utilization is above 30%, consider lowering your balance or increasing your limit."
    else:
        narrative += "Credit utilization looks within a healthy range."
    return narrative


@app.get('/healthz')
def health():
    return {'ok': True}

@app.get('/api/insights/{user_id}', response_model=InsightsResponse)
def insights(user_id: str):
    # simple cache check
    cache_key = f'insights:{user_id}'
    cached = cache.get(cache_key)
    if cached and (date.today() - cached['ts']).seconds < CACHE_TTL:
        return cached['payload']

    try:
        user, accts, txns = fetch_user_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'Upstream error: {e}')

    feats = engineer_features(accts, txns)
    narrative = gemini_narrative_safe(feats, user)

    payload = InsightsResponse(
        user_id=user_id,
        period={'from': (date.today() - timedelta(days=30)).isoformat(), 'to': date.today().isoformat()},
        summary=feats['summary'],
        categories=feats['categories'],
        merchants_top=feats['merchants_top'],
        credit_utilization=feats['credit_utilization'],
        narrative=narrative
    )
    cache[cache_key] = {'ts': date.today(), 'payload': payload}
    return payload
