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

The backend will use Supabase for data storage. Ensure your `.env` file contains valid Supabase credentials.

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

To seed sample data to your Supabase instance:

```bash
source venv/bin/activate
python scripts/seed_supabase.py
```

This creates sample colleges (UW + WSU campuses) with reviews.

## API Endpoints

- `GET /v0/colleges/search?q=query` — Search colleges
- `GET /v0/colleges/filter?...` — Filter & sort colleges
- `GET /v0/colleges/{slug}` — Get college with ratings
- `GET /v0/colleges/{slug}/reviews` — Get college reviews
- `POST /v0/reviews` — Submit a review
- `POST /v0/emails` — Subscribe to updates

## Supabase Configuration

The backend uses Supabase for data storage. Required environment variables in `.env`:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
```

To set up Supabase:

1. Create a project at https://supabase.com
2. Create the required tables:
   - `colleges` — College information
   - `accessibility_info` — Accessibility details
   - `university_summary` — University overview
   - `reviews` — User reviews
3. Copy your project URL, anon key, and JWT secret to `.env`
4. Run `python scripts/seed_supabase.py` to populate sample data


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
