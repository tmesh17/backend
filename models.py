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
    university_type = Column(String, nullable=True)  # e.g., "Public Research University"
    brand_color = Column(String, nullable=True)  # Hex color for university branding (e.g., "#4B0082" for UW purple)
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

    # Step 1: University and Role
    relationship_to_university = Column(String, nullable=True)  # current_student, former_student, alumni, faculty, staff, other
    attendance_start_year = Column(Integer, nullable=True)
    attendance_end_year = Column(Integer, nullable=True)

    # Step 2: Overall Rating
    accessibility_rating = Column(Float, nullable=True)  # 1-5
    safety_rating = Column(Float, nullable=True)  # 1-5
    inclusivity_rating = Column(Float, nullable=True)  # 1-5

    # Step 3: Written Experience
    experience_text = Column(String, nullable=True)  # What they want others to know

    # Step 4: Topics (comma-separated list)
    topics = Column(String, nullable=True)  # disability_services, physical_accessibility, housing, etc.

    # Step 5: Category Ratings (stored as JSON string)
    category_ratings = Column(String, nullable=True)  # JSON: {disability_services: 4, academic_accomodations: 5, ...}

    # Step 6: Optional Reviewer Context (all optional)
    age_category = Column(String, nullable=True)  # 18-25, 26-35, 36-50, 50+
    race_ethnicity = Column(String, nullable=True)  # predefined categories
    race_ethnicity_text = Column(String, nullable=True)  # optional text entry
    first_generation_student = Column(String, nullable=True)  # yes, no
    disability_identity = Column(String, nullable=True)  # text entry
    lgbtq_identity = Column(String, nullable=True)  # text entry

    created_at = Column(DateTime, server_default=func.now())


class UniversitySummary(Base):
    """
    Stores basic campus overview information from College Scorecard and other sources.
    One-to-one relationship with College via college_slug.
    """
    __tablename__ = "university_summary"

    id = Column(Integer, primary_key=True, index=True)
    college_slug = Column(String, unique=True, index=True, nullable=False)
    
    # Basic info
    website_url = Column(String, nullable=True)
    school_type = Column(String, nullable=True)  # e.g., "4-year", "2-year"
    
    # Enrollment
    total_enrollment = Column(Integer, nullable=True)  # Total number of students
    
    # Academic info
    undergrad_enrollment = Column(Integer, nullable=True)  # Undergraduate students
    
    # Degrees awarded
    degrees_awarded = Column(String, nullable=True)  # e.g., "Bachelor's, Master's, Doctorate"
    
    # Control/ownership
    school_ownership = Column(String, nullable=True)  # e.g., "Public", "Private nonprofit", "Private for-profit"
    
    created_at = Column(DateTime, server_default=func.now())


class UniversityAccessibilityInfo(Base):
    """
    Stores accessibility information from CeDaR and other sources.
    Flexible schema to handle variable data per college.
    One-to-one relationship with College via college_slug.
    """
    __tablename__ = "university_accessibility_info"

    id = Column(Integer, primary_key=True, index=True)
    college_slug = Column(String, unique=True, index=True, nullable=False)
    
    # Disability services contact info
    dso_phone = Column(String, nullable=True)  # Disability Services Office phone
    dso_email = Column(String, nullable=True)  # Disability Services Office email
    dso_url = Column(String, nullable=True)    # Disability Services Office website
    
    # On-campus resources
    has_disability_cultural_center = Column(Integer, default=0)  # 0 or 1
    has_deaf_culture_center = Column(Integer, default=0)         # 0 or 1
    has_disability_studies_program = Column(Integer, default=0)  # 0 or 1
    has_asl_program = Column(Integer, default=0)                 # 0 or 1
    
    # Accommodations & services (stored as comma-separated strings)
    accommodations_provided = Column(String, nullable=True)      # e.g., "Extended test time, Note-taking services, ASL interpreters"
    
    # Campus accessibility
    campus_accessibility_notes = Column(String, nullable=True)   # Free-form text about accessible features
    
    # Other resources
    counseling_services = Column(String, nullable=True)          # e.g., "On-campus counseling available"
    health_services = Column(String, nullable=True)              # e.g., "On-campus health center"
    
    created_at = Column(DateTime, server_default=func.now())


class EmailSubscription(Base):
    __tablename__ = "email_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
