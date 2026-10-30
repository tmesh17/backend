"""
FastAPI backend for College Score.

Implements all endpoints the frontend expects:
  GET  /v0/colleges/search?q=...
  GET  /v0/colleges/filter?sort_by=...&state=...
  GET  /v0/colleges/{slug}
  GET  /v0/colleges/{slug}/reviews
  POST /v0/reviews
  POST /v0/emails
  GET  /v0/colleges/compare?slugs=slug1,slug2,slug3  (new — for compare feature)

Run with: uvicorn main:app --reload --port 8000
"""
import os
import uuid
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv

from database import engine, Base, get_db
from models import College, Review, EmailSubscription
from schemas import (
    ReviewSubmission,
    EmailSubmission,
    EmailResponse,
)
from auth import verify_token

load_dotenv()

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="College Score API", version="0.1.0")

# CORS: allow the frontend (Next.js dev server) to call this API
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper: serialize a College ORM object into the JSON shape the frontend expects
# ---------------------------------------------------------------------------
def college_to_dict(college: College, db: Session) -> dict:
    review_count = (
        db.query(func.count(Review.id))
        .filter(Review.college_slug == college.slug)
        .scalar()
        or 0
    )

    ratings = {}
    if college.a11y_overall is not None:
        ratings["a11y_overall"] = college.a11y_overall
    if college.safety_overall is not None:
        ratings["safety_overall"] = college.safety_overall
    if college.inclusivity_overall is not None:
        ratings["inclusivity_overall"] = college.inclusivity_overall

    return {
        "id": college.id,
        "slug": college.slug,
        "name": college.name,
        "city": college.city,
        "state": college.state,
        "ratings": ratings if ratings else None,
        "num_reviews": review_count,
    }


def review_to_dict(review: Review) -> dict:
    """Serialize a Review ORM object into the JSON shape the frontend expects."""
    # Compute aggregate ratings from individual rating fields
    a11y_fields = [
        review.campus_accessibility,
        review.accommodations_reliability,
        review.disability_community_access,
    ]
    a11y_vals = [v for v in a11y_fields if v is not None]

    safety_vals = [review.campus_safety] if review.campus_safety is not None else []

    incl_fields = [
        review.peer_inclusivity,
        review.institution_inclusivity,
        review.student_language,
        review.staff_language,
    ]
    incl_vals = [v for v in incl_fields if v is not None]

    ratings = {
        "a11y_overall": round(sum(a11y_vals) / len(a11y_vals), 2) if a11y_vals else 0,
        "safety_overall": round(sum(safety_vals) / len(safety_vals), 2) if safety_vals else 0,
        "inclusivity_overall": round(sum(incl_vals) / len(incl_vals), 2) if incl_vals else 0,
    }

    # Parse identities from comma-separated string to list
    identities = review.identities.split(",") if review.identities else []

    return {
        "id": review.id,
        "review_date": review.review_date,
        "identities": identities,
        "share_accommodations_text": review.share_accommodations_text,
        "share_positive_text": review.share_positive_text,
        "share_challenges_text": review.share_challenges_text,
        "share_groups_text": review.share_groups_text,
        "ratings": ratings,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/v0/colleges/search")
def search_colleges(q: str, db: Session = Depends(get_db)):
    """Search colleges by name, city, or state. Returns array of College objects."""
    query_filter = f"%{q}%"
    colleges = (
        db.query(College)
        .filter(
            (College.name.ilike(query_filter))
            | (College.city.ilike(query_filter))
            | (College.state.ilike(query_filter))
        )
        .all()
    )
    return [college_to_dict(c, db) for c in colleges]


@app.get("/v0/colleges/filter")
def filter_colleges(
    sort_by: Optional[str] = None,
    state: Optional[str] = None,
    has_disability_cultural_center: Optional[bool] = None,
    min_safety: Optional[float] = None,
    min_inclusivity: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Filter and sort colleges based on criteria. Returns array of College objects."""
    query = db.query(College)

    if state:
        query = query.filter(College.state == state)
    if has_disability_cultural_center:
        query = query.filter(College.has_disability_cultural_center == 1)
    if min_safety is not None:
        query = query.filter(College.safety_overall >= min_safety)
    if min_inclusivity is not None:
        query = query.filter(College.inclusivity_overall >= min_inclusivity)

    colleges = query.all()

    # Sort
    if sort_by == "a11y_high_low":
        colleges.sort(key=lambda c: c.a11y_overall or 0, reverse=True)
    elif sort_by == "alphabetical":
        colleges.sort(key=lambda c: c.name)

    return [college_to_dict(c, db) for c in colleges]


@app.get("/v0/colleges/compare")
def compare_colleges(slugs: str, db: Session = Depends(get_db)):
    """
    New endpoint for the compare feature.
    Accepts comma-separated slugs and returns College objects with ratings + review counts.
    Usage: /v0/colleges/compare?slugs=slug1,slug2,slug3
    """
    slug_list = [s.strip() for s in slugs.split(",") if s.strip()]
    colleges = db.query(College).filter(College.slug.in_(slug_list)).all()
    return [college_to_dict(c, db) for c in colleges]


@app.get("/v0/colleges/{slug}")
def get_college(slug: str, db: Session = Depends(get_db)):
    """Get a single college by slug. Returns College object with ratings and review count."""
    college = db.query(College).filter(College.slug == slug).first()
    if not college:
        raise HTTPException(status_code=404, detail=f"College not found: {slug}")
    return college_to_dict(college, db)


@app.get("/v0/colleges/{slug}/reviews")
def get_college_reviews(slug: str, db: Session = Depends(get_db)):
    """Get all reviews for a college by slug. Returns array of ReviewEntry objects."""
    college = db.query(College).filter(College.slug == slug).first()
    if not college:
        raise HTTPException(status_code=404, detail=f"College not found: {slug}")

    reviews = db.query(Review).filter(Review.college_slug == slug).all()
    return [review_to_dict(r) for r in reviews]


@app.post("/v0/reviews")
def submit_review(
    submission: ReviewSubmission,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Submit a review. Requires a valid Supabase JWT in the Authorization header.
    The frontend sends: { answers: { ... } }
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token. Please sign in.",
        )

    token = authorization.replace("Bearer ", "")
    user = verify_token(token)  # Raises 401 if invalid

    answers = submission.answers
    college_slug = answers.get("college_slug")
    if not college_slug:
        raise HTTPException(
            status_code=400,
            detail="college_slug is required in answers.",
        )

    # Verify the college exists
    college = db.query(College).filter(College.slug == college_slug).first()
    if not college:
        raise HTTPException(
            status_code=404,
            detail=f"College not found: {college_slug}",
        )

    # Create the review
    def to_int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def to_list_str(val):
        if isinstance(val, list):
            return ",".join(str(v) for v in val)
        return str(val) if val is not None else None

    def to_float(val):
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    review = Review(
        id=str(uuid.uuid4()),
        college_slug=college_slug,
        review_date="2025-01-15",  # Could use actual current date
        identities=None,  # Could derive from lgbtq_identity, poc_identity, disability_identity
        share_accommodations_text=answers.get("share_accommodations"),
        share_positive_text=answers.get("share_positive"),
        share_challenges_text=answers.get("share_challenges"),
        share_groups_text=answers.get("share_community_groups"),
        campus_safety=to_float(answers.get("campus_safety")),
        peer_inclusivity=to_float(answers.get("peer_inclusivity")),
        institution_inclusivity=to_float(answers.get("institution_inclusivity")),
        student_language=to_float(answers.get("student_language")),
        staff_language=to_float(answers.get("staff_language")),
        campus_accessibility=to_float(answers.get("campus_accessibility")),
        disability_community_access=to_float(answers.get("disability_community_access")),
        accommodations_reliability=to_float(answers.get("accommodations_reliability")),
        attendance_start=to_int(answers.get("attendance_start")),
        attendance_end=to_int(answers.get("attendance_end")),
        use_a11y_services=answers.get("use_a11y_services"),
        is_lgbtq=answers.get("is_lgbtq"),
        lgbtq_identity=to_list_str(answers.get("lgbtq_identity")),
        is_poc=answers.get("is_poc"),
        poc_identity=to_list_str(answers.get("poc_identity")),
        is_disabled=answers.get("is_disabled"),
        disability_identity=to_list_str(answers.get("disability_identity")),
    )

    # Build identities list from demographic answers
    identities = []
    if review.lgbtq_identity and review.is_lgbtq == "yes":
        identities.extend(review.lgbtq_identity.split(","))
    if review.poc_identity and review.is_poc == "yes":
        identities.extend(review.poc_identity.split(","))
    if review.disability_identity and review.is_disabled == "yes":
        identities.extend(review.disability_identity.split(","))
    review.identities = ",".join(identities) if identities else None

    db.add(review)
    db.commit()

    # Update the college's aggregate ratings
    _update_college_ratings(db, college)

    db.commit()

    return {"message": "Review submitted successfully", "review_id": review.id}


@app.post("/v0/emails", response_model=EmailResponse)
def add_email(submission: EmailSubmission, db: Session = Depends(get_db)):
    """Add an email to the subscription list."""
    existing = (
        db.query(EmailSubscription)
        .filter(EmailSubscription.email == submission.email)
        .first()
    )
    if existing:
        return EmailResponse(message="You are already subscribed!")

    email_sub = EmailSubscription(email=submission.email)
    db.add(email_sub)
    db.commit()

    return EmailResponse(message="Successfully subscribed!")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _update_college_ratings(db: Session, college: College):
    """Recalculate and store aggregate ratings from all reviews for a college."""
    reviews = db.query(Review).filter(Review.college_slug == college.slug).all()
    if not reviews:
        return

    def avg(vals):
        nums = [v for v in vals if v is not None]
        return round(sum(nums) / len(nums), 2) if nums else None

    # Accessibility = average of campus_accessibility, accommodations_reliability, disability_community_access
    a11y_all = []
    for r in reviews:
        a11y_all.extend([r.campus_accessibility, r.accommodations_reliability, r.disability_community_access])
    college.a11y_overall = avg(a11y_all)

    # Safety
    safety_vals = [r.campus_safety for r in reviews if r.campus_safety is not None]
    college.safety_overall = avg(safety_vals)

    # Inclusivity = average of peer_inclusivity, institution_inclusivity, student_language, staff_language
    incl_all = []
    for r in reviews:
        incl_all.extend([r.peer_inclusivity, r.institution_inclusivity, r.student_language, r.staff_language])
    college.inclusivity_overall = avg(incl_all)
