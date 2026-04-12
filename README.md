# WalletAce

A credit card recommendation engine that takes a short survey about your spending habits, credit profile, and preferences — then returns the top 2 cards personalised for you.

---

## How it works

1. **Survey** — user answers questions about income, FICO score, monthly spending across 8 categories, and preferences (airline, hotel, annual fee tolerance)
2. **Eligibility filter** — cards that don't match the user's credit tier, income, Chase 5/24 status, or intro APR requirement are removed
3. **EANV scoring** — each eligible card is scored by Estimated Annual Net Value (rewards earned across all categories minus annual fee, plus sign-up bonus if year 1)
4. **AI ranking** — DeepSeek reviews the top candidates and selects the best 2 with a plain-English explanation
5. **Business rules** — rank 1 is always the best general (non-co-branded) card; rank 2 is the best preference-matched airline/hotel card if the user stated a preference

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Recommendation API | FastAPI (Python 3.11), port 8000 |
| Cards data API | FastAPI (Python 3.11), port 8001 |
| Database | Neon (serverless PostgreSQL) via asyncpg |
| Session cache | Upstash Redis |
| AI ranking | DeepSeek (`deepseek-chat`) via OpenAI-compatible SDK |
| Card sync | APScheduler — weekly cron, Sundays 02:00 UTC |

---

## Project structure

```
WalletAce/
├── frontend/                        # React app (port 5173)
│   └── src/
│       ├── pages/                   # LandingPage, SurveyPage, ResultsPage
│       ├── components/              # Survey inputs, result cards, progress bar
│       ├── data/questions.ts        # All survey question definitions
│       ├── types/survey.ts          # SurveyState interface
│       └── api/recommend.ts         # API call to recommendation-service
│
├── backend/
│   ├── cards-service/               # Card catalogue + survey storage (port 8001)
│   │   ├── app/
│   │   │   ├── routers/
│   │   │   │   ├── cards.py         # GET /api/v1/cards
│   │   │   │   ├── survey_responses.py  # POST /api/v1/survey-responses
│   │   │   │   ├── admin.py         # POST /admin/sync (manual card sync)
│   │   │   │   └── health.py        # GET /health
│   │   │   └── sync/
│   │   │       └── card_syncer.py   # DeepSeek batch fetch + DB upsert
│   │   ├── migrations/
│   │   │   ├── 001_create_cards_table.sql
│   │   │   ├── 002_add_card_name_unique.sql
│   │   │   └── 003_create_survey_responses.sql
│   │   └── scripts/
│   │       └── fetch_cards.py       # One-shot card population script
│   │
│   └── recommendation-service/      # Recommendation engine (port 8000)
│       └── app/
│           ├── engine/
│           │   ├── eligibility.py   # Phase 1 — FICO, 5/24, income, fee, APR filters
│           │   ├── eanv.py          # Phase 2 — Estimated Annual Net Value scoring
│           │   ├── llm_ranker.py    # Phase 3 — DeepSeek AI ranking
│           │   └── ranking.py       # Rule-based fallback ranker
│           ├── routers/
│           │   └── recommend.py     # POST /api/v1/recommend
│           ├── models/
│           │   ├── survey.py        # UserSurvey Pydantic model + enums
│           │   └── card.py          # Card model
│           └── cache/
│               └── redis_client.py  # Session cache wrapper
│
└── docker-compose.yml               # Local Docker setup (Redis + both services)
```

---

## Local setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Access to a Neon PostgreSQL database
- An Upstash Redis instance
- A DeepSeek API key (get one at https://platform.deepseek.com)

---

### 1. Environment files

Create a `.env` file in each backend directory.

**`backend/cards-service/.env`**
```env
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<neon-host>/walletace?sslmode=require
DEEPSEEK_API_KEY=sk-...
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
```

**`backend/recommendation-service/.env`**
```env
CARDS_SERVICE_URL=http://localhost:8001
REDIS_URL=rediss://default:<password>@<upstash-host>:6379
DEEPSEEK_API_KEY=sk-...
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
```

**`frontend/.env`**
```env
VITE_API_URL=http://localhost:8000
```

---

### 2. Install dependencies

Run once per service the first time.

```bash
# cards-service
cd backend/cards-service
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

# recommendation-service
cd backend/recommendation-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# frontend
cd frontend
npm install
```

---

### 3. Run database migrations

Open the **Neon SQL Editor** and run these in order:

1. `backend/cards-service/migrations/001_create_cards_table.sql`
2. `backend/cards-service/migrations/002_add_card_name_unique.sql`
3. `backend/cards-service/migrations/003_create_survey_responses.sql`

This only needs to be done once on a fresh database.

---

### 4. Start all three services

Open 3 separate terminals.

**Terminal 1 — cards-service** (port 8001)
```bash
cd backend/cards-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

**Terminal 2 — recommendation-service** (port 8000)
```bash
cd backend/recommendation-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 3 — frontend** (port 5173)
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**

---

### 5. Seed card data (first run only)

After the services are running, trigger a card sync to populate the database:

```bash
curl -X POST http://localhost:8001/admin/sync
```

This calls DeepSeek in 5 batches and upserts ~50 cards. Takes about 2 minutes. You'll see a JSON response like `{"upserted": 50, "skipped": 0}` when done.

To verify:
```bash
curl http://localhost:8001/api/v1/cards | python -c "import json,sys; cards=json.load(sys.stdin); print(f'{len(cards)} cards loaded')"
```

---

## API reference

### `POST /api/v1/recommend`
Main recommendation endpoint on the recommendation-service (port 8000).

**Request body** — UserSurvey with 20 fields including:
- `fico_tier` — `lt_580 | 580_669 | 670_739 | 740_799 | 800_850`
- `annual_income`, `monthly_groceries`, `monthly_dining`, etc.
- `willing_to_pay_fee`, `max_annual_fee` (0–1000)
- `airline_preference`, `hotel_preference`
- `needs_intro_apr`, `prefers_cash_back`

**Query param** — `?year=1` (always year 1; sign-up bonus included)

**Response** — top 2 `CardResult` objects with EANV, category breakdown, and `why_this_card` explanation.

### `GET /api/v1/cards`
Returns the full card catalogue from cards-service (port 8001).

### `POST /admin/sync`
Manually triggers the weekly card sync (DeepSeek fetch + DB upsert).

---

## Card sync

The card catalogue is kept fresh by a weekly cron job (Sundays 02:00 UTC) that:

1. Calls DeepSeek in 5 batches to fetch ~50 real US credit cards
2. Each batch prompt includes an explicit exclusion list of all prior batch cards to prevent duplicates
3. Deduplicates by `card_name` in Python before writing (last batch wins on conflict)
4. Upserts via `ON CONFLICT (issuer, card_name)` — new cards are inserted, existing cards update only their affiliate link if it was a placeholder
5. Overwrites all `affiliate_link` values with verified real issuer URLs from a hardcoded dict

---

## Database schema

**`cards`** — the card catalogue (populated by sync)

**`survey_requests`** — one row per survey submission (flat columns, no JSON)

**`survey_results`** — recommendation output linked to each request via FK, with all rec1/rec2 fields stored flat

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Make sure venv is activated before running uvicorn |
| cards-service returns 503 from recommendation-service | Start cards-service first; check it's on port 8001 |
| Empty card list | Run `POST /admin/sync` to seed the DB |
| Redis connection error | Check `REDIS_URL` in recommendation-service `.env` |
| No recommendations returned (422) | User's FICO tier or income may not match any cards — try a higher credit tier in the survey |
| Duplicate Delta Reserve card in DB | Run `POST /admin/sync` — the upsert will collapse the duplicate |
