# College Score Backend

FastAPI server for the College Score application.

## Quick Start

### Prerequisites

- Python 3.9+
- pip or conda

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Required** — Supabase credentials:
- `SUPABASE_URL` — Your Supabase project URL
- `SUPABASE_SECRET_KEY` — Your Supabase secret key

**Optional** — College Scorecard API (for importing 6,000+ US colleges):
- `SCORECARD_API_KEY` — Get free key from [api.data.gov/signup](https://api.data.gov/signup/)

### 3. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive API docs: `http://localhost:8000/docs`

## Running with Frontend

The frontend runs on `http://localhost:3001` and the backend on `http://127.0.0.1:8000`. Both must run simultaneously in separate terminal windows.

### Terminal 1: Backend

```bash
cd backend/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3001`.

## Database Seeding

To seed sample data (test colleges + 6,000+ US colleges from College Scorecard API):

```bash
source venv/bin/activate
python seed.py
```

This will:
- Create 2 test colleges (UW Seattle, WSU Spokane) with sample reviews
- Fetch ~6,000 US colleges from the College Scorecard API
- Insert all colleges into the database

**To enable College Scorecard import:**

1. Get a free API key from [api.data.gov/signup](https://api.data.gov/signup/)
2. Add to `.env`:
   ```
   SCORECARD_API_KEY=your-key-here
   ```
3. Re-run `python seed.py`

The seed script will:
- Always import test colleges with full data
- Skip if `SCORECARD_API_KEY` is not set
- Safely handle re-runs (won't duplicate existing colleges)

## API Endpoints

- `GET /v0/colleges/search?q=query` — Search colleges
- `GET /v0/colleges/filter?...` — Filter & sort colleges
- `GET /v0/colleges/{slug}` — Get college with ratings
- `GET /v0/colleges/{slug}/reviews` — Get college reviews
- `POST /v0/reviews` — Submit a review
- `POST /v0/emails` — Subscribe to updates

## Configuration

### Supabase Setup

The backend uses Supabase for data storage. Required environment variables in `.env`:

```
SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key
SUPABASE_DISCOVERY_URL=your_supabase_discovery_url
```

Tables are created automatically when you run `python seed.py`.

### College Scorecard API (Optional)

To import all ~6,000 US colleges:

1. Get a free API key: [api.data.gov/signup](https://api.data.gov/signup/)
2. Add to `.env`: `SCORECARD_API_KEY=your-key`
3. Run: `python seed.py`


## Troubleshooting

**Backend port already in use?**
```bash
kill -9 $(lsof -ti:8000)
```

**Frontend port already in use?**
```bash
kill -9 $(lsof -ti:3001)
```

**Database connection errors?**
- Verify your Supabase credentials in `.env`
- Check that all required tables exist in your Supabase project
- Ensure your Supabase project is running and accessible

**CORS errors when frontend calls backend?**
- The backend is configured to accept requests from `http://localhost:3001`
- Ensure both frontend and backend are running
- Check browser console for specific error messages

## Project Structure

- `main.py` — FastAPI app with all routes
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic request/response models
- `app/services/` — Business logic
- `database.py` — Database connection setup
- `auth.py` — JWT verification
- `scripts/seed_supabase.py` — Database seeding script
