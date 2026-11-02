"""
Seed script: populates the database with UW and WSU colleges plus sample reviews.

Run with: python seed.py
Safe to run multiple times (uses get_or_create pattern).
"""
import uuid
from database import SessionLocal, engine, Base
from models import College, Review

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


# Each entry: (college_slug, identities, accommodations, positive, challenges, groups,
#              campus_safety, peer_inclusivity, institution_inclusivity,
#              student_language, staff_language, campus_accessibility,
#              disability_community_access, accommodations_reliability)
REVIEWS = [
    # --- UW Seattle ---
    ("university-of-washington-seattle-campus-seattle-wa",
     ["Wheelchair User", "LGBTQ+"], "I use a wheelchair and received accessible housing near my classes. The DRS office was responsive but the process took several weeks.",
     "I felt very supported by my peers and found a welcoming community in the DRC student group.",
     "Some older buildings on campus are not wheelchair accessible, which made navigating to certain classes difficult.",
     "DRC student group, ASUW Disability Awareness group",
     4, 5, 4, 4, 5, 3, 4, 4),

    ("university-of-washington-seattle-campus-seattle-wa",
     ["Chronic Health Condition"], "I receive extended test time and note-taking assistance. The accommodations have been reliable once approved.",
     "The faculty has been very understanding and willing to work with me on flexible deadlines.",
     "Getting accommodations initially set up required a lot of self-advocacy and paperwork.",
     "Disability Studies class, Chronic Illness Support Group",
     5, 4, 4, 5, 4, 4, 3, 5),

    ("university-of-washington-seattle-campus-seattle-wa",
     ["Mental Health Condition", "POC"],
     "I use mental health accommodations including flexible attendance. The counseling center has been helpful.",
     "I found a strong community through the ECC (Ethnic Cultural Center) and counseling services.",
     "The wait times for counseling appointments can be long, sometimes several weeks.",
     "ECC, Black Student Union, NAMI on Campus",
     3, 4, 5, 3, 4, 5, 3, 3),

    # --- WSU Spokane ---
    ("washington-state-university-spokane-campus-spokane-wa",
     ["Mental Health Condition"],
     "I receive accommodations for anxiety including flexible deadlines and a quiet space for exams.",
     "The health sciences campus is very supportive and the class sizes are small enough that faculty know you personally.",
     "Limited mental health resources on the Spokane campus compared to Pullman.",
     "Wellness group, pharmacy student support network",
     5, 5, 5, 4, 5, 5, 3, 4),

    ("washington-state-university-spokane-campus-spokane-wa",
     ["Hearing Impairment"],
     "I use ASL interpreters and captioning services. The DRS office coordinated everything well.",
     "The campus is modern and accessible, and faculty have been responsive to my needs.",
     "Finding ASL interpreters for certain specialized courses was sometimes challenging.",
     "Deaf community meetups, ASL Club",
     4, 4, 4, 5, 5, 5, 4, 4),

    ("washington-state-university-spokane-campus-spokane-wa",
     ["Learning Disability", "ADHD"],
     "I receive extended test time and a quiet testing environment. The Disability Support Services office is easy to reach.",
     "The smaller campus size made it easier to connect with faculty and get to know my classmates.",
     "There are fewer disability-specific student groups compared to larger campuses.",
     "DSS peer mentoring, study skills workshops",
     4, 4, 5, 4, 5, 4, 3, 5),
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
        identities, accommodations, positive, challenges, groups,
        campus_safety, peer_inclusivity, institution_inclusivity,
        student_language, staff_language, campus_accessibility,
        disability_community_access, accommodations_reliability
    ) = data

    review = Review(
        id=str(uuid.uuid4()),
        college_slug=slug,
        review_date="2025-01-15",
        identities=",".join(identities) if identities else None,
        share_accommodations_text=accommodations,
        share_positive_text=positive,
        share_challenges_text=challenges,
        share_groups_text=groups,
        campus_safety=campus_safety,
        peer_inclusivity=peer_inclusivity,
        institution_inclusivity=institution_inclusivity,
        student_language=student_language,
        staff_language=staff_language,
        campus_accessibility=campus_accessibility,
        disability_community_access=disability_community_access,
        accommodations_reliability=accommodations_reliability,
    )
    db.add(review)
    return review


def update_college_ratings(db, slug):
    """Compute and store aggregate ratings from all reviews for a college."""
    reviews = db.query(Review).filter(Review.college_slug == slug).all()
    if not reviews:
        return

    def avg(field):
        vals = [getattr(r, field) for r in reviews if getattr(r, field) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    college = db.query(College).filter(College.slug == slug).first()
    if college:
        # Accessibility = average of campus_accessibility, accommodations_reliability, disability_community_access
        a11y_vals = [r.campus_accessibility for r in reviews if r.campus_accessibility]
        acc_vals = [r.accommodations_reliability for r in reviews if r.accommodations_reliability]
        dcc_vals = [r.disability_community_access for r in reviews if r.disability_community_access]
        all_a11y = a11y_vals + acc_vals + dcc_vals
        college.a11y_overall = round(sum(all_a11y) / len(all_a11y), 2) if all_a11y else None

        # Safety = average of campus_safety
        safety_vals = [r.campus_safety for r in reviews if r.campus_safety]
        college.safety_overall = round(sum(safety_vals) / len(safety_vals), 2) if safety_vals else None

        # Inclusivity = average of peer_inclusivity, institution_inclusivity, student_language, staff_language
        incl_vals = [r.peer_inclusivity for r in reviews if r.peer_inclusivity]
        inst_vals = [r.institution_inclusivity for r in reviews if r.institution_inclusivity]
        stud_vals = [r.student_language for r in reviews if r.student_language]
        staff_vals = [r.staff_language for r in reviews if r.staff_language]
        all_incl = incl_vals + inst_vals + stud_vals + staff_vals
        college.inclusivity_overall = round(sum(all_incl) / len(all_incl), 2) if all_incl else None


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Seed colleges
    for c in COLLEGES:
        get_or_create_college(db, c)

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
    print(f"  - {len(REVIEWS)} reviews")


if __name__ == "__main__":
    run_seed()
