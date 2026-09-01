# Secure Auth & LLM API — Profile Bio Extractor

A secure, containerized RESTful API built with **FastAPI** that implements robust user authentication via **Supabase Auth** and integrates a production-grade, fault-tolerant **LLM endpoint** for structured metadata extraction.

---

## 🏗️ Architecture & Security

* **Backend Framework:** FastAPI (Python 3.10+)
* **Identity Provider:** Supabase Auth (Stateless JWT via Bearer Authorization)
* **LLM Integration:** OpenAI SDK connected via OpenRouter (`openrouter/free` / `LLM_MODEL`)
* **Production Safety & Reliability:** 
  * **Strict Schema Validation:** Pydantic models enforce exact closed enums (`engineering`, `design`, `product`, `other`) and field boundaries.
  * **Self-Repair Retry Loop:** 1-shot repair mechanism feeds exact Pydantic validation errors back to the LLM upon malformed responses before quarantine.
  * **Hard Timeouts & Exponential Backoff:** 30-second client timeouts with automatic exponential backoff retries for rate limits (429) and provider errors (5xx).
  * **Telemetry & Cost Tracking:** Automated per-request logging of token usage, latency, and repair counts to `logs/cost.jsonl`.
  * **Quarantine Logging:** Failed model outputs after retry exhaustion are safely isolated in `logs/quarantine.jsonl` and return a clean `422 Unprocessable Entity`.
  * **Emergency Kill Switch & Stub Mode:** Zero-downtime kill switch via `LLM_ENABLED` and mock development via `LLM_STUB`.

---

## 📋 Job Card: Profile Bio Extractor

* **What it does:** Extracts structured professional metadata (job title, experience years, role category, and confidence score) from messy, unstructured user bios.
* **Input Contract:**
  ```json
  {
    "text": "string, 1-1000 characters"
  }
  ```
* **Output Schema Contract:**
  ```json
  {
    "job_title": "string or null",
    "years_experience": "integer or null",
    "category": "one of [engineering|design|product|other]",
    "confidence": "0.0-1.0"
  }
  ```
* **Strict Constraints:**
  * Must **never** invent categories outside the allowed enum list.
  * Must **never** guess years of experience if not explicitly mentioned.
  * Must **never** return markdown formatting or conversational text outside the raw JSON.
  * When uncertain, safely defaults to `"other"` with low confidence.

---

## 🚀 Quick Start Guide

### 1. Environment Variables

Create your `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Configure your environment variables:

```env
# Supabase Authentication
SUPABASE_URL="your-supabase-url"
SUPABASE_KEY="your-supabase-anon-key"

# LLM Pipeline Configuration
LLM_BASE_URL="https://openrouter.ai/api/v1"
LLM_API_KEY="your-openrouter-api-key"
LLM_MODEL="openrouter/free"
LLM_STUB="0"
LLM_ENABLED="true"
```

### 2. Launch the Application

#### Option A: Run Locally with Uvicorn
```bash
uvicorn src.main:app --reload
```

#### Option B: Run with Docker Compose
```bash
docker compose up --build
```

---

## 🌐 API Reference & Usage

### Extract Bio Endpoint

* **Method:** `POST`
* **Path:** `/extract-bio`
* **Content-Type:** `application/json`

#### Example Request:
```bash
curl -X POST http://127.0.0.1:8000/extract-bio \
  -H "Content-Type: application/json" \
  -d '{"text": "Backend engineer with 5 years experience building scalable microservices."}'
```

#### Expected 200 OK Response:
```json
{
  "job_title": "Backend Engineer",
  "years_experience": 5,
  "category": "engineering",
  "confidence": 0.98
}
```

---

## 📊 Evaluation Results & Metrics

The extraction pipeline is evaluated against a 12-case benchmark suite in [evals/cases.json](file:///c:/Users/Haroon%20Traders/Desktop/Flyrank%20AI/Backend%20Eng/A2/evals/cases.json) covering standard career fields, ambiguous phrasing, non-professional text, and boundary edge cases.

### Running Evaluations
```bash
python evals/run.py
```

### Evaluation Results:
* **Prompt Version:** `v1` ([prompts/extract-bio-v1.md](file:///c:/Users/Haroon%20Traders/Desktop/Flyrank%20AI/Backend%20Eng/A2/prompts/extract-bio-v1.md))
* **Dataset Size:** 12 test cases (3 Engineering, 3 Design, 3 Product, 3 Other)
* **Success Score:** **12/12 (100% Accuracy & Schema Compliance)**

### Cost & Performance Summary (from `logs/cost.jsonl`):
* **Average Latency:** ~2,000 – 4,000 ms per live model inference
* **Average Token Usage:** ~300 prompt tokens / ~150 completion tokens per extraction
* **Estimated Cost:** $0.00 (leveraging OpenRouter free-tier models with `temperature=0.0` determinism)