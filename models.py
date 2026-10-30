"""
SQLAlchemy ORM models for College, Review, and EmailSubscription.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base


class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    # Aggregated rating fields (computed from reviews, stored for quick lookup)
    a11y_overall = Column(Float, nullable=True)
    safety_overall = Column(Float, nullable=True)
    inclusivity_overall = Column(Float, nullable=True)
    # Whether the college has a disability cultural center
    has_disability_cultural_center = Column(Integer, default=0)  # 0 or 1 (bool)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, index=True)  # UUID
    college_slug = Column(String, index=True, nullable=False)
    review_date = Column(String, nullable=False)  # ISO date string

    # Identity tags stored as comma-separated string
    identities = Column(String, nullable=True)

    # Free-response text fields
    share_accommodations_text = Column(String, nullable=True)
    share_positive_text = Column(String, nullable=True)
    share_challenges_text = Column(String, nullable=True)
    share_groups_text = Column(String, nullable=True)

    # Rating fields (individual review, 1-5 scale)
    campus_safety = Column(Float, nullable=True)
    peer_inclusivity = Column(Float, nullable=True)
    institution_inclusivity = Column(Float, nullable=True)
    student_language = Column(Float, nullable=True)
    staff_language = Column(Float, nullable=True)
    campus_accessibility = Column(Float, nullable=True)
    disability_community_access = Column(Float, nullable=True)
    accommodations_reliability = Column(Float, nullable=True)

    # Demographic fields
    attendance_start = Column(Integer, nullable=True)
    attendance_end = Column(Integer, nullable=True)
    use_a11y_services = Column(String, nullable=True)
    is_lgbtq = Column(String, nullable=True)
    lgbtq_identity = Column(String, nullable=True)
    is_poc = Column(String, nullable=True)
    poc_identity = Column(String, nullable=True)
    is_disabled = Column(String, nullable=True)
    disability_identity = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())


class EmailSubscription(Base):
    __tablename__ = "email_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
