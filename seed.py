"""
Seed script: populates the database with UW and WSU colleges plus sample reviews.

Run with: python seed.py
Safe to run multiple times (uses get_or_create pattern).
"""
import uuid
from database import SessionLocal, engine, Base
from models import College, Review, UniversityAccessibilityInfo, UniversitySummary

# Import models so Base knows about all tables before create_all
import models  # noqa: F401


COLLEGES = [
    {
        "id": 236948,
        "slug": "university-of-washington-seattle-campus-seattle-wa",
        "name": "University of Washington-Seattle Campus",
        "city": "Seattle",
        "state": "WA",
        "university_type": "Public Research University",
        "brand_color": "#4B0082",  # UW Purple
        "has_disability_cultural_center": 1,
    },
    {
        "id": 236940,
        "slug": "washington-state-university-spokane-campus-spokane-wa",
        "name": "Washington State University-Spokane Campus",
        "city": "Spokane",
        "state": "WA",
        "university_type": "Public Research University",
        "brand_color": "#981E32",  # WSU Crimson
        "has_disability_cultural_center": 0,
    },
]


# Accessibility info pulled from CeDaR database
ACCESSIBILITY_INFO = [
    {
        "college_slug": "university-of-washington-seattle-campus-seattle-wa",
        "dso_phone": "(206) 543-8925",
        "dso_email": "uwdrs@uw.edu",
        "dso_url": "https://depts.washington.edu/uwdrs/",
        "has_disability_cultural_center": 1,
        "has_deaf_culture_center": 1,
        "has_disability_studies_program": 1,
        "has_asl_program": 1,
        "accommodations_provided": "Extended test time, Note-taking services, ASL interpreters, Accessible housing, Class attendance flexibility, Alternative format materials, Exam proctoring",
        "campus_accessibility_notes": "Campus has accessible buildings with elevators, ramps, and accessible restrooms. Accessible parking available near major buildings.",
        "counseling_services": "UW Counseling Center provides mental health services including crisis support",
        "health_services": "Harborview Medical Center and UW Medical Center on-campus and nearby",
    },
    {
        "college_slug": "washington-state-university-spokane-campus-spokane-wa",
        "dso_phone": "(509) 358-7865",
        "dso_email": "drs.spokane@wsu.edu",
        "dso_url": "https://spokane.wsu.edu/student-services/disability-services/",
        "has_disability_cultural_center": 0,
        "has_deaf_culture_center": 0,
        "has_disability_studies_program": 0,
        "has_asl_program": 0,
        "accommodations_provided": "Extended test time, Note-taking services, ASL interpreters available upon request, Accessible housing, Flexible attendance policies",
        "campus_accessibility_notes": "Modern Spokane campus with accessible facilities. Most buildings meet ADA standards.",
        "counseling_services": "Counseling and Psychological Services (CAPS) available for students",
        "health_services": "Student Health Services on campus",
    },
]


# University summary info from College Scorecard API
UNIVERSITY_SUMMARY = [
    {
        "college_slug": "university-of-washington-seattle-campus-seattle-wa",
        "website_url": "https://www.washington.edu/",
        "school_type": "4-year",
        "total_enrollment": 47000,
        "undergrad_enrollment": 32000,
        "degrees_awarded": "Bachelor's, Master's, Doctorate",
        "school_ownership": "Public",
    },
    {
        "college_slug": "washington-state-university-spokane-campus-spokane-wa",
        "website_url": "https://spokane.wsu.edu/",
        "school_type": "4-year",
        "total_enrollment": 3500,
        "undergrad_enrollment": 2200,
        "degrees_awarded": "Bachelor's, Master's",
        "school_ownership": "Public",
    },
]


# Each entry: (college_slug, relationship, start_year, end_year, a11y_rating, safety_rating, inclusivity_rating, 
#              experience_text, topics, category_ratings, age, race, first_gen, disability, lgbtq)
REVIEWS = [
    # --- UW Seattle ---
    ("university-of-washington-seattle-campus-seattle-wa",
     "current_student", 2022, 2026,
     4, 4, 5,
     "UW has been welcoming overall. The Disability Resources for Students office is helpful, though response times can be slow. Accessibility varies by building - some newer facilities are great, older ones have challenges.",
     "disability_services,physical_accessibility,academic_accomodations",
     '{"disability_services": 4, "academic_accomodations": 4, "physical_accessibility": 3, "accessible_housing": 4}',
     "18-25", "Asian", "no", "Deaf", ""),

    ("university-of-washington-seattle-campus-seattle-wa",
     "alumni", 2018, 2022,
     3, 5, 4,
     "My time at UW was positive. Campus is generally safe and inclusive. Housing accommodations for disabled students are available but limited. Professors were understanding about extensions.",
     "academic_accomodations,campus_culture,housing",
     '{"transportation": 5, "digital_accessibility": 4, "lgbtq_inclusion": 5, "campus_diversity": 4}',
     "26-35", "Hispanic/Latino", "yes", "ADHD", ""),

    ("university-of-washington-seattle-campus-seattle-wa",
     "current_student", 2023, 2027,
     4, 4, 4,
     "Good experience so far. LGBTQ+ community is strong here. Accessibility services are decent but sometimes bureaucratic. Would recommend.",
     "lgbtq_inclusion,safety,campus_culture",
     '{"racial_cultural_inclusion": 5, "religious_tolerance": 4, "peer_support": 5, "liberal_climate": 5}',
     "18-25", "White", "no", "", "She/her, Bisexual"),

    # --- WSU Spokane ---
    ("washington-state-university-spokane-campus-spokane-wa",
     "current_student", 2021, 2025,
     5, 5, 5,
     "Spokane campus is smaller and more tight-knit. Disability services are responsive and helpful. Campus is very accessible. Great experience overall.",
     "disability_services,physical_accessibility",
     '{"disability_services": 5, "physical_accessibility": 5, "accessible_housing": 4, "digital_accessibility": 5}',
     "18-25", "Indigenous", "yes", "Mobility disability", ""),

    ("washington-state-university-spokane-campus-spokane-wa",
     "former_student", 2019, 2023,
     4, 5, 5,
     "Campus was welcoming. Good transportation options. Housing was comfortable. Overall positive experience.",
     "transportation,housing,campus_culture",
     '{"transportation": 4, "accessible_housing": 4, "campus_diversity": 5, "lgbtq_inclusion": 4}',
     "26-35", "Black/African American", "yes", "", "He/him, Gay"),

    ("washington-state-university-spokane-campus-spokane-wa",
     "staff", 2020, None,
     4, 4, 4,
     "Working here, I see the institution taking accessibility seriously. Good commitment to inclusion. Could use more LGBTQ+ specific resources.",
     "lgbtq_inclusion,safety,academic_accomodations",
     '{"racial_cultural_inclusion": 4, "religious_tolerance": 3, "peer_support": 4, "liberal_climate": 3}',
     None, None, None, "Neurotypical", "She/her, Asexual"),
]


def get_or_create_college(db, college_data):
    college = db.query(College).filter(College.slug == college_data["slug"]).first()
    if college:
        return college
    college = College(**college_data)
    db.add(college)
    db.commit()
    return college


def create_review(db, slug, data):
    (
        relationship, start_year, end_year, a11y_rating, safety_rating, inclusivity_rating,
        experience_text, topics, category_ratings, age, race, first_gen, disability, lgbtq
    ) = data

    review = Review(
        id=str(uuid.uuid4()),
        college_slug=slug,
        review_date="2025-01-15",
        relationship_to_university=relationship,
        attendance_start_year=start_year,
        attendance_end_year=end_year,
        accessibility_rating=a11y_rating,
        safety_rating=safety_rating,
        inclusivity_rating=inclusivity_rating,
        experience_text=experience_text,
        topics=topics,
        category_ratings=category_ratings,
        age_category=age,
        race_ethnicity=race,
        first_generation_student=first_gen,
        disability_identity=disability,
        lgbtq_identity=lgbtq,
    )
    db.add(review)
    return review


def update_college_ratings(db, slug):
    """Compute and store aggregate ratings from all reviews for a college."""
    reviews = db.query(Review).filter(Review.college_slug == slug).all()
    if not reviews:
        return

    def avg(vals):
        nums = [v for v in vals if v is not None]
        return round(sum(nums) / len(nums), 2) if nums else None

    college = db.query(College).filter(College.slug == slug).first()
    if college:
        # Accessibility rating
        a11y_vals = [r.accessibility_rating for r in reviews if r.accessibility_rating is not None]
        college.a11y_overall = avg(a11y_vals)

        # Safety rating
        safety_vals = [r.safety_rating for r in reviews if r.safety_rating is not None]
        college.safety_overall = avg(safety_vals)

        # Inclusivity rating
        incl_vals = [r.inclusivity_rating for r in reviews if r.inclusivity_rating is not None]
        college.inclusivity_overall = avg(incl_vals)


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Seed colleges
    for c in COLLEGES:
        get_or_create_college(db, c)

    # Seed accessibility info
    for info in ACCESSIBILITY_INFO:
        existing = db.query(UniversityAccessibilityInfo).filter(
            UniversityAccessibilityInfo.college_slug == info["college_slug"]
        ).first()
        if not existing:
            accessibility_info = UniversityAccessibilityInfo(**info)
            db.add(accessibility_info)

    # Seed university summary info
    for summary in UNIVERSITY_SUMMARY:
        existing = db.query(UniversitySummary).filter(
            UniversitySummary.college_slug == summary["college_slug"]
        ).first()
        if not existing:
            univ_summary = UniversitySummary(**summary)
            db.add(univ_summary)

    db.commit()

    # Seed reviews
    for slug, *data in REVIEWS:
        create_review(db, slug, data)

    db.commit()

    # Update aggregate ratings (after commit so reviews are persisted)
    for c in COLLEGES:
        update_college_ratings(db, c["slug"])
    db.commit()  # Commit the rating updates
    db.close()
    print("Database seeded successfully!")
    print(f"  - {len(COLLEGES)} colleges")
    print(f"  - {len(ACCESSIBILITY_INFO)} accessibility info entries")
    print(f"  - {len(UNIVERSITY_SUMMARY)} university summary entries")
    print(f"  - {len(REVIEWS)} reviews")


if __name__ == "__main__":
    run_seed()
