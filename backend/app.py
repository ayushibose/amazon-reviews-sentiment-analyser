from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import re

# --- NLTK for lightweight sentiment analysis ---
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
nltk.download("vader_lexicon")


sia = SentimentIntensityAnalyzer()



app = FastAPI(title="Sentiment API")

# ⚠ For MVP: open CORS. Tighten later to only your extension/domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple neutral heuristic: if confidence < 0.60, call it NEUTRAL
NEUTRAL_THRESHOLD = 0.60

class PredictIn(BaseModel):
    text: str

class PredictBatchIn(BaseModel):
    texts: List[str]

def classify(text: str) -> Dict[str, Any]:
    scores = sia.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.06:
        label = "POSITIVE"
    elif compound <= -0.04:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
    return {"sentiment": label, "confidence": abs(compound)}


@app.get("/health")
def health():
    return {"ok": True}

@app.post("/predict")
def predict(body: PredictIn):
    return classify(body.text)

@app.post("/predict_batch")
def predict_batch(body: PredictBatchIn):
    return {"results": [classify(t) for t in body.texts]}


# ===== Ingestion and Analytics Store =====

class ReviewResult(BaseModel):
    sentiment: str
    confidence: float
    text: str
    date: Optional[str] = None  # raw date string from the site
    country: Optional[str] = None  # country of origin from review

class IngestResultsBody(BaseModel):
    asin: str
    title: str
    results: List[ReviewResult]

# In-memory store: { asin: { "title": str, "results": [ReviewResult...], "updated_at": iso } }
DATA_STORE: Dict[str, Dict[str, Any]] = {}

@app.post("/ingest_results")
def ingest_results(body: IngestResultsBody):
    asin = body.asin.strip().upper()
    if len(asin) != 10:
        raise HTTPException(status_code=400, detail="Invalid ASIN")

    if asin not in DATA_STORE:
        DATA_STORE[asin] = {
            "title": body.title,
            "results": [],
            "updated_at": datetime.utcnow().isoformat(),
        }
    # Append; do not dedupe for MVP
    DATA_STORE[asin]["results"].extend([r.model_dump() for r in body.results])
    DATA_STORE[asin]["title"] = body.title or DATA_STORE[asin]["title"]
    DATA_STORE[asin]["updated_at"] = datetime.utcnow().isoformat()
    return {"ok": True, "stored": len(body.results)}


@app.get("/products")
def list_products():
    summaries = []
    for asin, payload in DATA_STORE.items():
        results = payload.get("results", [])
        counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        for r in results:
            s = r.get("sentiment")
            if s in counts:
                counts[s] += 1
        summaries.append({
            "asin": asin,
            "title": payload.get("title", asin),
            "updated_at": payload.get("updated_at"),
            "review_count": len(results),
            "counts": counts,
        })
    return {"products": summaries}


@app.get("/product/{asin}")
def get_product(asin: str):
    asin = asin.strip().upper()
    if asin not in DATA_STORE:
        raise HTTPException(status_code=404, detail="Unknown ASIN")
    return {"asin": asin, **DATA_STORE[asin]}


@app.get("/timeseries/{asin}")
def timeseries(asin: str):
    asin = asin.strip().upper()
    if asin not in DATA_STORE:
        raise HTTPException(status_code=404, detail="Unknown ASIN")
    results = DATA_STORE[asin]["results"]
    # Aggregate by date (best-effort parse); fallback group as unknown
    buckets: Dict[str, Dict[str, int]] = {}
    def normalize_date(raw: str) -> str:
        s = (raw or "").strip()
        if not s:
            return "UNKNOWN"
        # If string contains pattern like "Reviewed in X on 5 August 2025"
        m = re.search(r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})", s)
        if m:
            date_text = m.group(1)
            for fmt in ("%d %B %Y", "%d %b %Y"):
                try:
                    return datetime.strptime(date_text, fmt).date().isoformat()
                except Exception:
                    pass
        # Try US style: Month DD, YYYY
        m2 = re.search(r"([A-Za-z]+\s+\d{1,2},\s*\d{4})", s)
        if m2:
            date_text = m2.group(1)
            for fmt in ("%B %d, %Y", "%b %d, %Y"):
                try:
                    return datetime.strptime(date_text, fmt).date().isoformat()
                except Exception:
                    pass
        # Try ISO directly
        try:
            return datetime.fromisoformat(s).date().isoformat()
        except Exception:
            return s  # fallback raw bucket

    for r in results:
        raw = r.get("date")
        key = normalize_date(raw)
        if key not in buckets:
            buckets[key] = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        s = r.get("sentiment", "NEUTRAL")
        if s not in buckets[key]:
            buckets[key][s] = 0
        buckets[key][s] += 1
    # Sort keys if possible
    def sort_key(k: str):
        try:
            return datetime.fromisoformat(k)
        except Exception:
            return k
    labels = sorted(buckets.keys(), key=sort_key)
    return {
        "asin": asin,
        "labels": labels,
        "positive": [buckets[k].get("POSITIVE", 0) for k in labels],
        "neutral": [buckets[k].get("NEUTRAL", 0) for k in labels],
        "negative": [buckets[k].get("NEGATIVE", 0) for k in labels],
    }

@app.get("/country_sentiment/{asin}")
def country_sentiment(asin: str):
    asin = asin.strip().upper()
    if asin not in DATA_STORE:
        raise HTTPException(status_code=404, detail="Unknown ASIN")
    results = DATA_STORE[asin]["results"]
    
    # Aggregate by country
    country_buckets: Dict[str, Dict[str, int]] = {}
    for r in results:
        country = r.get("country", "Unknown")
        if country not in country_buckets:
            country_buckets[country] = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        sentiment = r.get("sentiment", "NEUTRAL")
        if sentiment not in country_buckets[country]:
            country_buckets[country][sentiment] = 0
        country_buckets[country][sentiment] += 1
    
    return {
        "asin": asin,
        "countries": list(country_buckets.keys()),
        "positive": [country_buckets[c].get("POSITIVE", 0) for c in country_buckets.keys()],
        "neutral": [country_buckets[c].get("NEUTRAL", 0) for c in country_buckets.keys()],
        "negative": [country_buckets[c].get("NEGATIVE", 0) for c in country_buckets.keys()],
    }

# Optional: serve a simple index to point users to Streamlit app instructions
@app.get("/")
def root():
    return {
        "message": "Sentiment API running.",
        "docs": "/docs",
        "dashboard": "Run: streamlit run dashboard.py",
    }
