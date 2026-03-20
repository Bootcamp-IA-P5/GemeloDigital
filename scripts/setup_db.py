
import os
import sys
import json
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, SessionLocal, init_db
from app.models import Course

def seed_courses():
    """Seeds the courses table from data/seed/courses.json"""
    seed_path = os.path.join("data", "seed", "courses.json")
    if not os.path.exists(seed_path):
        print(f"❌ Seed file not found at {seed_path}")
        return

    print(f"🌱 Seeding courses from {seed_path}...")
    with open(seed_path, "r", encoding="utf-8") as f:
        courses_data = json.load(f)

    db: Session = SessionLocal()
    try:
        count = 0
        for item in courses_data:
            # Check if course already exists
            existing = db.query(Course).filter(Course.id == item["id"]).first()
            if not existing:
                course = Course(
                    id=item["id"],
                    title=item["title"],
                    description=item["description"],
                    url=item.get("url"),
                    competencies=item.get("competencies", []),
                    level=item.get("level", "beginner"),
                    duration_hours=item.get("duration_hours", 0),
                    trajectory_affinity=item.get("trajectory_affinity", "both")
                )
                db.add(course)
                count += 1
        
        db.commit()
        print(f"✅ Seeded {count} new courses.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding courses: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Re-initializing database (dropping and recreating tables)...")
    try:
        # Drop all tables to apply schema changes (UUID -> String)
        Base.metadata.drop_all(bind=engine)
        init_db()
        seed_courses()
        print("✨ Database setup complete!")
    except Exception as e:
        print(f"💥 Fatal error during setup: {e}")
        print("\n💡 TIP: Make sure your DATABASE_URL in .env is correct and PostgreSQL is running.")
