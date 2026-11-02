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
from models import College, Review, EmailSubscription, UniversityAccessibilityInfo, UniversitySummary
from schemas import (
    ReviewSubmission,
    EmailSubmission,
    EmailResponse,
)

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
def accessibility_info_to_dict(accessibility_info: UniversityAccessibilityInfo) -> dict:
    """Serialize accessibility info, only including non-null fields."""
    if not accessibility_info:
        return {}
    
    result = {}
    if accessibility_info.dso_phone:
        result["dso_phone"] = accessibility_info.dso_phone
    if accessibility_info.dso_email:
        result["dso_email"] = accessibility_info.dso_email
    if accessibility_info.dso_url:
        result["dso_url"] = accessibility_info.dso_url
    if accessibility_info.has_disability_cultural_center:
        result["has_disability_cultural_center"] = bool(accessibility_info.has_disability_cultural_center)
    if accessibility_info.has_deaf_culture_center:
        result["has_deaf_culture_center"] = bool(accessibility_info.has_deaf_culture_center)
    if accessibility_info.has_disability_studies_program:
        result["has_disability_studies_program"] = bool(accessibility_info.has_disability_studies_program)
    if accessibility_info.has_asl_program:
        result["has_asl_program"] = bool(accessibility_info.has_asl_program)
    if accessibility_info.accommodations_provided:
        result["accommodations_provided"] = [
            a.strip() for a in accessibility_info.accommodations_provided.split(",")
        ]
    if accessibility_info.campus_accessibility_notes:
        result["campus_accessibility_notes"] = accessibility_info.campus_accessibility_notes
    if accessibility_info.counseling_services:
        result["counseling_services"] = accessibility_info.counseling_services
    if accessibility_info.health_services:
        result["health_services"] = accessibility_info.health_services
    
    return result if result else None


def university_summary_to_dict(summary: UniversitySummary) -> dict:
    """Serialize university summary, only including non-null fields."""
    if not summary:
        return {}
    
    result = {}
    if summary.website_url:
        result["website_url"] = summary.website_url
    if summary.school_type:
        result["school_type"] = summary.school_type
    if summary.total_enrollment:
        result["total_enrollment"] = summary.total_enrollment
    if summary.undergrad_enrollment:
        result["undergrad_enrollment"] = summary.undergrad_enrollment
    if summary.degrees_awarded:
        result["degrees_awarded"] = [
            d.strip() for d in summary.degrees_awarded.split(",")
        ]
    if summary.school_ownership:
        result["school_ownership"] = summary.school_ownership
    
    return result if result else None


def calculate_category_rating_averages(college_slug: str, db: Session) -> dict:
    """Calculate average ratings for each category based on all reviews for this college."""
    import json
    
    reviews = db.query(Review).filter(Review.college_slug == college_slug).all()
    if not reviews:
        return {}
    
    # Aggregate all category ratings
    category_totals = {}
    category_counts = {}
    
    for review in reviews:
        if review.category_ratings:
            try:
                ratings = json.loads(review.category_ratings)
                for category, rating in ratings.items():
                    if category not in category_totals:
                        category_totals[category] = 0
                        category_counts[category] = 0
                    category_totals[category] += rating
                    category_counts[category] += 1
            except:
                pass
    
    # Calculate averages
    averages = {}
    for category, total in category_totals.items():
        count = category_counts[category]
        averages[category] = {
            "average": round(total / count, 2),
            "count": count
        }
    
    return averages


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

    # Fetch accessibility info for this college
    accessibility_info = (
        db.query(UniversityAccessibilityInfo)
        .filter(UniversityAccessibilityInfo.college_slug == college.slug)
        .first()
    )

    # Fetch university summary for this college
    university_summary = (
        db.query(UniversitySummary)
        .filter(UniversitySummary.college_slug == college.slug)
        .first()
    )

    result = {
        "id": college.id,
        "slug": college.slug,
        "name": college.name,
        "city": college.city,
        "state": college.state,
        "university_type": college.university_type,
        "brand_color": college.brand_color,
        "ratings": ratings if ratings else None,
        "num_reviews": review_count,
    }
    
    # Include accessibility info if available
    a11y_dict = accessibility_info_to_dict(accessibility_info)
    if a11y_dict:
        result["accessibility_info"] = a11y_dict
    
    # Include university summary if available
    summary_dict = university_summary_to_dict(university_summary)
    if summary_dict:
        result["university_summary"] = summary_dict
    
    # Include category rating averages if available
    category_ratings = calculate_category_rating_averages(college.slug, db)
    if category_ratings:
        result["category_rating_averages"] = category_ratings
    
    return result


def review_to_dict(review: Review) -> dict:
    """Serialize a Review ORM object into the JSON shape the frontend expects."""
    import json
    
    ratings = {
        "accessibility": review.accessibility_rating or 0,
        "safety": review.safety_rating or 0,
        "inclusivity": review.inclusivity_rating or 0,
    }

    # Parse category ratings from JSON if available
    category_ratings = {}
    if review.category_ratings:
        try:
            category_ratings = json.loads(review.category_ratings)
        except:
            pass

    # Parse topics from comma-separated string
    topics = review.topics.split(",") if review.topics else []

    return {
        "id": review.id,
        "review_date": review.review_date,
        "relationship_to_university": review.relationship_to_university,
        "attendance_start_year": review.attendance_start_year,
        "attendance_end_year": review.attendance_end_year,
        "ratings": ratings,
        "experience_text": review.experience_text,
        "topics": topics,
        "category_ratings": category_ratings,
        "reviewer_context": {
            "age_category": review.age_category,
            "race_ethnicity": review.race_ethnicity,
            "race_ethnicity_text": review.race_ethnicity_text,
            "first_generation_student": review.first_generation_student,
            "disability_identity": review.disability_identity,
            "lgbtq_identity": review.lgbtq_identity,
        },
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
    Submit a review. Authentication is optional.
    The frontend sends: { answers: { ... } }
    """
    import json
    
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

    # Helper functions for type conversion
    def to_float(val):
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def to_int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def to_str(val):
        if isinstance(val, list):
            return ",".join(str(v) for v in val)
        return str(val) if val is not None else None

    # Build category_ratings JSON
    category_ratings = {}
    rating_mappings = {
        "disability_services_rating": "disability_services",
        "academic_accomodations_rating": "academic_accomodations",
        "physical_accessibility_rating": "physical_accessibility",
        "accessible_housing_rating": "accessible_housing",
        "transportation_rating": "transportation",
        "digital_accessibility_rating": "digital_accessibility",
        "lgbtq_inclusion_rating": "lgbtq_inclusion",
        "racial_cultural_inclusion_rating": "racial_cultural_inclusion",
        "religious_tolerance_rating": "religious_tolerance",
        "campus_diversity_rating": "campus_diversity",
        "peer_support_rating": "peer_support",
        "liberal_climate_rating": "liberal_climate",
    }
    
    for question_id, field_name in rating_mappings.items():
        if question_id in answers:
            rating_val = to_float(answers[question_id])
            if rating_val is not None:
                category_ratings[field_name] = rating_val

    # Create the review with new schema
    review = Review(
        id=str(uuid.uuid4()),
        college_slug=college_slug,
        review_date="2025-01-15",
        relationship_to_university=answers.get("relationship_to_university"),
        attendance_start_year=to_int(answers.get("attendance_years_start")),
        attendance_end_year=to_int(answers.get("attendance_years_end")),
        accessibility_rating=to_float(answers.get("accessibility_rating")),
        safety_rating=to_float(answers.get("safety_rating")),
        inclusivity_rating=to_float(answers.get("inclusivity_rating")),
        experience_text=answers.get("experience_text"),
        topics=to_str(answers.get("topics")),
        category_ratings=json.dumps(category_ratings) if category_ratings else None,
        age_category=answers.get("age_category"),
        race_ethnicity=answers.get("race_ethnicity"),
        race_ethnicity_text=answers.get("race_ethnicity_text"),
        first_generation_student=answers.get("first_generation_student"),
        disability_identity=answers.get("disability_identity"),
        lgbtq_identity=answers.get("lgbtq_identity"),
    )

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

    # Accessibility = average of accessibility_rating
    a11y_vals = [r.accessibility_rating for r in reviews if r.accessibility_rating is not None]
    college.a11y_overall = avg(a11y_vals)

    # Safety = average of safety_rating
    safety_vals = [r.safety_rating for r in reviews if r.safety_rating is not None]
    college.safety_overall = avg(safety_vals)

    # Inclusivity = average of inclusivity_rating
    incl_vals = [r.inclusivity_rating for r in reviews if r.inclusivity_rating is not None]
    college.inclusivity_overall = avg(incl_vals)
