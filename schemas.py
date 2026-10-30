"""
Pydantic schemas for request bodies and response serialization.
"""
from pydantic import BaseModel
from typing import Optional


class CollegeResponse(BaseModel):
    """Returned by search, filter, and get college endpoints."""
    id: int
    slug: str
    name: str
    city: str
    state: str
    ratings: Optional[dict] = None  # {a11y_overall, safety_overall, inclusivity_overall}
    num_reviews: Optional[int] = None

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Returned by the get-college-reviews endpoint."""
    id: str
    college_slug: str
    review_date: str
    identities: Optional[list[str]] = None
    share_accommodations_text: Optional[str] = None
    share_positive_text: Optional[str] = None
    share_challenges_text: Optional[str] = None
    share_groups_text: Optional[str] = None
    ratings: dict  # {a11y_overall, safety_overall, inclusivity_overall}

    class Config:
        from_attributes = True


class ReviewSubmission(BaseModel):
    """Request body for POST /v0/reviews."""
    answers: dict


class EmailSubmission(BaseModel):
    """Request body for POST /v0/emails."""
    email: str


class EmailResponse(BaseModel):
    message: str
