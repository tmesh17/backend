# College Score Backend

FastAPI server for the College Score application.

## Setup

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

### 3. Seed the Database

```bash
python seed.py
```

This creates 6 colleges (UW + WSU campuses) with 10 sample reviews.

### 4. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive API docs: `http://localhost:8000/docs`

## API Endpoints

- `GET /v0/colleges/search?q=query` — Search colleges
- `GET /v0/colleges/filter?...` — Filter & sort colleges
- `GET /v0/colleges/{slug}` — Get college with ratings
- `GET /v0/colleges/{slug}/reviews` — Get college reviews
- `POST /v0/reviews` — Submit a review (requires auth)
- `POST /v0/emails` — Subscribe to updates

## Project Structure

- `main.py` — FastAPI app with all routes
- `models.py` — SQLAlchemy ORM models
- `schemas.py` — Pydantic request/response models
- `database.py` — Database setup
- `auth.py` — JWT verification
- `seed.py` — Database seeding

## Supabase Setup (Optional)

For review submission with authentication:

1. Create a Supabase project at https://supabase.com
2. Enable email/password authentication
3. Copy JWT Secret from Settings > API
4. Add to `.env`: `SUPABASE_JWT_SECRET=your-secret`

Without this, the backend accepts any review in dev mode.

## Troubleshooting

**Port already in use?**
```bash
kill -9 $(lsof -ti:8000)
```

**Database errors?**
```bash
rm collegescore.db
python seed.py
```

**Need to add more colleges?**
Edit `seed.py`, update `COLLEGES` and `REVIEWS`, then re-seed.
