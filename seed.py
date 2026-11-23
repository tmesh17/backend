"""
Seed script: populates the database with UW and WSU colleges plus sample reviews,
then fetches additional colleges from College Scorecard API.

Features:
- Keeps 2 test colleges (UW Seattle, WSU Spokane) with full sample data + reviews
- Fetches ~7,000 colleges from College Scorecard API
- Matches with CeDaR accessibility data (where available)
- Uses get_or_create pattern to safely run multiple times

Run with: python seed.py
Requires: SCORECARD_API_KEY environment variable (get from https://api.data.gov)

Safe to run multiple times (existing colleges and reviews preserved).
"""
import uuid
import requests
import os
import json
from typing import Optional, Dict, List
from database import SessionLocal, engine, Base
from models import College, Review, UniversityAccessibilityInfo, UniversitySummary

# Import models so Base knows about all tables before create_all
import models  # noqa: F401
from integrations import ENRICH_TEST_COLLEGES


# ============================================================================
# HARDCODED TEST COLLEGES (kept with full data)
# ============================================================================

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
        "ipeds_unitid": "236948",  # IPEDS UnitID from College Scorecard
        "county_fips": "53033",     # King County, WA
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
        "ipeds_unitid": "236940",  # IPEDS UnitID from College Scorecard
        "county_fips": "53063",     # Spokane County, WA
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


# ============================================================================
# COLLEGE SCORECARD API FUNCTIONS
# ============================================================================

def _decode_ownership(ownership_code: Optional[int]) -> Optional[str]:
    """Decode school ownership from code."""
    ownership = {1: "Public", 2: "Private nonprofit", 3: "Private for-profit"}
    return ownership.get(ownership_code)


def fetch_colleges_from_scorecard(api_key: str, limit: Optional[int] = None) -> List[Dict]:
    """
    Fetch college data from College Scorecard API.
    
    Fetches: name, city, state, school_type, control (ownership), total_enrollment,
             undergrad_enrollment, degrees_awarded, website_url
    
    Args:
        api_key: API key from https://api.data.gov
        limit: Max colleges to fetch (None = all ~7,000)
    
    Returns:
        List of college dicts
    """
    BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
    
    colleges = []
    page = 0
    per_page = 100
    
    print(f"Fetching colleges from College Scorecard API...")
    
    while True:
        # College Scorecard fields we want (simplified)
        # Use dot notation to access nested fields
        fields = [
            "id",
            "school.name",
            "school.city",
            "school.state",
            "school.school_url",
            "school.ownership",  # 1=Public, 2=Private nonprofit, 3=Private for-profit
            "latest.student.size",  # Total enrollment
        ]
        
        params = {
            "api_key": api_key,
            "per_page": per_page,
        }
        
        # Only add select if fields are specified
        if fields:
            params["_fields"] = ",".join(fields)
        
        # Pagination
        params["page"] = page
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"  Error fetching page {page}: {e}")
            break
        
        if "results" not in data or not data["results"]:
            break
        
        for result in data["results"]:
            try:
                # API returns flat structure with dot notation keys
                college = {
                    "id": result.get("id"),
                    "name": result.get("school.name"),
                    "city": result.get("school.city"),
                    "state": result.get("school.state"),
                    "website_url": result.get("school.school_url"),
                    "school_type": "4-year",  # Default
                    "school_ownership": _decode_ownership(result.get("school.ownership")),
                    "total_enrollment": result.get("latest.student.size"),
                    "undergrad_enrollment": None,
                    "degrees_awarded": None,
                }
                
                # Only add if has required fields
                if college["id"] and college["name"] and college["state"]:
                    colleges.append(college)
            except Exception as e:
                continue
        
        print(f"  Loaded {len(colleges)} colleges (page {page + 1})...")
        
        if limit and len(colleges) >= limit:
            colleges = colleges[:limit]
            break
        
        page += 1
    
    print(f"Total colleges fetched: {len(colleges)}")
    return colleges


# ============================================================================
# CEDAR DATABASE INTEGRATION (PLACEHOLDER)
# ============================================================================

def match_with_cedar_data(college: Dict) -> Optional[Dict]:
    """
    Match college with CeDaR accessibility data.
    
    TODO: Integrate with actual CeDaR database
    For now, returns None (no accessibility data available)
    
    CeDaR provides:
    - DSO contact info (phone, email, URL)
    - Disability cultural center status
    - Deaf culture center status
    - On-campus accommodations
    - Campus accessibility notes
    
    Args:
        college: College dict from College Scorecard
    
    Returns:
        Accessibility info dict or None if not found
    """
    # Placeholder: would call CeDaR API or database here
    # For now, only test colleges have accessibility data
    return None


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def get_or_create_college(db, college_data: Dict):
    """Get existing college or create new one."""
    slug = college_data.get("slug")
    college = db.query(College).filter(College.slug == slug).first()
    if college:
        return college
    college = College(**college_data)
    db.add(college)
    db.commit()
    return college


def create_college_from_scorecard(db, scorecard_college: Dict) -> College:
    """
    Create college object from Scorecard data.
    
    Generates a slug from name, city, state.
    Extracts IPEDS UnitID from API response.
    """
    # Generate slug: lowercase, replace spaces with hyphens
    name = scorecard_college.get("name", "")
    city = scorecard_college.get("city", "")
    state = scorecard_college.get("state", "")
    slug = f"{name}-{city}-{state}".lower().replace(" ", "-").replace("--", "-")
    
    # IPEDS UnitID is the 'id' field from College Scorecard API
    ipeds_unitid = str(scorecard_college.get("id")) if scorecard_college.get("id") else None
    
    college_data = {
        "id": scorecard_college.get("id"),
        "slug": slug,
        "name": name,
        "city": city,
        "state": state,
        "university_type": None,  # Not in Scorecard
        "brand_color": None,       # Will be generated client-side
        "has_disability_cultural_center": 0,  # Default: unknown
        "ipeds_unitid": ipeds_unitid,  # 6-digit IPEDS UnitID
        "county_fips": None,  # Will be populated from Census Geocoder if available
    }
    
    return get_or_create_college(db, college_data)


def create_summary_from_scorecard(db, scorecard_college: Dict, college_slug: str):
    """Create UniversitySummary from Scorecard data."""
    existing = db.query(UniversitySummary).filter(
        UniversitySummary.college_slug == college_slug
    ).first()
    
    if existing:
        return
    
    summary = UniversitySummary(
        college_slug=college_slug,
        website_url=scorecard_college.get("website_url"),
        school_type=scorecard_college.get("school_type"),
        total_enrollment=scorecard_college.get("total_enrollment"),
        undergrad_enrollment=scorecard_college.get("undergrad_enrollment"),
        degrees_awarded=scorecard_college.get("degrees_awarded"),
        school_ownership=scorecard_college.get("school_ownership"),
    )
    db.add(summary)
    db.commit()


def create_review(db, slug: str, data):
    """Create a review from tuple data."""
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


def update_college_ratings(db, slug: str):
    """Compute and store aggregate ratings from all reviews for a college."""
    reviews = db.query(Review).filter(Review.college_slug == slug).all()
    if not reviews:
        return

    def avg(vals):
        nums = [v for v in vals if v is not None]
        return round(sum(nums) / len(nums), 2) if nums else None

    college = db.query(College).filter(College.slug == slug).first()
    if college:
        a11y_vals = [r.accessibility_rating for r in reviews if r.accessibility_rating is not None]
        college.a11y_overall = avg(a11y_vals)

        safety_vals = [r.safety_rating for r in reviews if r.safety_rating is not None]
        college.safety_overall = avg(safety_vals)

        incl_vals = [r.inclusivity_rating for r in reviews if r.inclusivity_rating is not None]
        college.inclusivity_overall = avg(incl_vals)


# ============================================================================
# MAIN SEED FUNCTION
# ============================================================================

def run_seed():
    """Main seed function."""
    print("=" * 70)
    print("COLLEGE SCORE DATABASE SEED")
    print("=" * 70)
    
    # Ensure tables exist with current schema
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Debug: verify tables were created
    try:
        db.query(College).count()
        db.query(UniversitySummary).count()
        db.query(UniversityAccessibilityInfo).count()
        print("✓ Database tables verified\n")
    except Exception as e:
        print(f"✗ Database initialization error: {e}")
        print("  Try deleting collegescore.db and running seed again\n")
        db.close()
        return

    # ========================================================================
    # PHASE 1: Seed hardcoded test colleges with full data
    # ========================================================================
    print("\n[PHASE 1] Seeding test colleges (UW Seattle, WSU Spokane)...")
    
    try:
        for c in COLLEGES:
            get_or_create_college(db, c)
        print(f"  ✓ {len(COLLEGES)} test colleges created/verified")

        # Seed accessibility info
        print("\n  Fetching city overview data for test colleges...")
        for info in ACCESSIBILITY_INFO:
            existing = db.query(UniversityAccessibilityInfo).filter(
                UniversityAccessibilityInfo.college_slug == info["college_slug"]
            ).first()
            
            if not existing:
                accessibility_info = UniversityAccessibilityInfo(**info)
            else:
                accessibility_info = existing
            
            # Fetch real city overview data - always refresh for test colleges
            college_data = None
            for college in COLLEGES:
                if college["slug"] == info["college_slug"]:
                    college_data = college
                    break
            
            if college_data:
                print(f"  Fetching city overview for {college_data['city']}, {college_data['state']}...")
                try:
                    from integrations import build_city_overview
                    city_overview = build_city_overview(college_data)
                    if city_overview:
                        accessibility_info.city_overview = json.dumps(city_overview)
                        print(f"  ✓ Stored city overview for {college_data['city']}, {college_data['state']}")
                    else:
                        print(f"  ✗ No city overview data returned for {college_data['city']}, {college_data['state']}")
                except Exception as e:
                    print(f"  ✗ Exception fetching city data: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  ⚠ College data not found for {info['college_slug']}")
            
            if not existing:
                db.add(accessibility_info)
        db.commit()
        print(f"  ✓ {len(ACCESSIBILITY_INFO)} accessibility info entries ready")

        # Seed university summary info
        print("\n  Fetching student demographics for test colleges...")
        for summary in UNIVERSITY_SUMMARY:
            existing = db.query(UniversitySummary).filter(
                UniversitySummary.college_slug == summary["college_slug"]
            ).first()
            
            if not existing:
                univ_summary = UniversitySummary(**summary)
            else:
                univ_summary = existing
            
            # Fetch real student demographics from College Scorecard API - always refresh for test colleges
            college_name = None
            for college in COLLEGES:
                if college["slug"] == summary["college_slug"]:
                    college_name = college["name"]
                    break
            
            if college_name:
                print(f"  Fetching student demographics for {college_name}...")
                try:
                    from integrations import fetch_college_student_demographics
                    demographics = fetch_college_student_demographics(college_name)
                    if demographics:
                        demographics.pop("source", None)  # Remove source before storing
                        univ_summary.student_demographics = json.dumps(demographics)
                        print(f"  ✓ Stored student demographics for {college_name}")
                    else:
                        print(f"  ✗ No student demographics returned for {college_name}")
                except Exception as e:
                    print(f"  ✗ Exception fetching demographics: {e}")
                    import traceback
                    traceback.print_exc()
            
            if not existing:
                db.add(univ_summary)
        db.commit()
        print(f"  ✓ {len(UNIVERSITY_SUMMARY)} university summary entries ready")

        # Seed reviews for test colleges
        for slug, *data in REVIEWS:
            create_review(db, slug, data)
        db.commit()
        print(f"  ✓ {len(REVIEWS)} reviews created for test colleges")

        # Update ratings
        for c in COLLEGES:
            update_college_ratings(db, c["slug"])
        db.commit()
        print(f"  ✓ Aggregate ratings calculated")
    
    except Exception as e:
        print(f"\n✗ PHASE 1 ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return

    # ========================================================================
    # PHASE 2: Fetch and seed colleges from College Scorecard API
    # ========================================================================
    print("\n[PHASE 2] Fetching colleges from College Scorecard API...")
    
    api_key = os.getenv("SCORECARD_API_KEY")
    if not api_key:
        print("  ⚠ SCORECARD_API_KEY not set. Skipping College Scorecard import.")
        print("  To enable: set SCORECARD_API_KEY in .env (get from https://api.data.gov)")
    else:
        try:
            # Fetch from Scorecard (None = all ~6,272 colleges)
            scorecard_colleges = fetch_colleges_from_scorecard(api_key, limit=None)
            
            print(f"\n[PHASE 2B] Processing {len(scorecard_colleges)} colleges from Scorecard...")
            
            colleges_created = 0
            for scorecard_college in scorecard_colleges:
                try:
                    # Skip if we already have this college (by ID)
                    existing = db.query(College).filter(
                        College.id == scorecard_college.get("id")
                    ).first()
                    if existing:
                        continue
                    
                    # Create college
                    college = create_college_from_scorecard(db, scorecard_college)
                    
                    # Create university summary
                    create_summary_from_scorecard(db, scorecard_college, college.slug)
                    
                    # Match with CeDaR data (if available)
                    cedar_data = match_with_cedar_data(scorecard_college)
                    if cedar_data:
                        existing_a11y = db.query(UniversityAccessibilityInfo).filter(
                            UniversityAccessibilityInfo.college_slug == college.slug
                        ).first()
                        if not existing_a11y:
                            a11y_info = UniversityAccessibilityInfo(
                                college_slug=college.slug,
                                **cedar_data
                            )
                            db.add(a11y_info)
                    
                    colleges_created += 1
                    
                except Exception as e:
                    print(f"    Error processing college: {e}")
                    continue
            
            db.commit()
            print(f"  ✓ {colleges_created} colleges from Scorecard imported")
        
        except Exception as e:
            print(f"  ✗ Error fetching from Scorecard: {e}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("SEED COMPLETE")
    print("=" * 70)
    
    db_session = SessionLocal()
    total_colleges = db_session.query(College).count()
    total_reviews = db_session.query(Review).count()
    db_session.close()
    
    print(f"✓ Total colleges in database: {total_colleges}")
    print(f"✓ Total reviews in database: {total_reviews}")
    print(f"✓ Test colleges: {len(COLLEGES)}")
    print(f"✓ Test reviews: {len(REVIEWS)}")
    print(f"✓ Accessibility info entries: {len(ACCESSIBILITY_INFO)}")
    print(f"✓ University summaries: {len(UNIVERSITY_SUMMARY)}")
    print("\nTo view API docs: http://localhost:8000/docs")
    print("To search colleges: http://localhost:3000")


if __name__ == "__main__":
    run_seed()
