import os
import sys
from dotenv import load_dotenv

# Fix Python Path
current_dir = os.path.dirname(os.path.abspath(__file__)) # agents/tools
root_dir = os.path.dirname(os.path.dirname(current_dir)) # project root
if root_dir not in sys.path:
    sys.path.append(root_dir)

from langchain_core.tools import tool
from app.database import SessionLocal, Base, engine
from app.models import User, Profile

load_dotenv()

@tool
def save_user_profile(user_id: str, profile_dict: dict) -> str:
    """
    Saves or updates a user's competency profile in the PostgreSQL database.
    Useful for persisting cognitive profiles after the Profiling Agent runs.
    
    Args:
        user_id (str): The unique ID of the user (String format expected by DB).
        profile_dict (dict): The generated profile containing competencies, recommended_approach, and summary.
    """
    print(f"\n[TOOL: Persistence] Attempting to save profile for user: {user_id}")
    
    db = SessionLocal()
    try:
        # 1. Verify user exists (or create a mock one for testing if needed)
        # Note: In a real app, the user would already exist from authentication.
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"[TOOL: Persistence] User {user_id} not found. Creating a mock user for this test run.")
            user = User(id=user_id, email=f"mock_{user_id}@test.com", password_hash="dummy")
            db.add(user)
            db.commit()

        # 2. Check if a profile already exists for this user
        existing_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        
        if existing_profile:
            # Update existing profile
            existing_profile.competency_profile = profile_dict
            existing_profile.avatar_personality = profile_dict.get("avatar_personality")
            existing_profile.avatar_color = profile_dict.get("avatar_color")
            print("[TOOL: Persistence] Updated existing profile.")
        else:
            # Create new profile
            new_profile = Profile(
                user_id=user_id,
                competency_profile=profile_dict,
                avatar_personality=profile_dict.get("avatar_personality"),
                avatar_color=profile_dict.get("avatar_color")
            )
            db.add(new_profile)
            print("[TOOL: Persistence] Created new profile.")
            
        db.commit()
        return "SUCCESS: User profile saved to database."
        
    except Exception as e:
        db.rollback()
        print(f"[TOOL: Persistence] Error saving profile: {e}")
        return f"Error saving to database: {str(e)}"
    finally:
        db.close()

if __name__ == "__main__":
    import uuid
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database tables ensured.")
    
    mock_id = str(uuid.uuid4())
    print("\n--- Testing Persistence Tool ---")
    mock_profile = {
        "competencies": [{"name": "Testing", "level": "alto"}],
        "recommended_approach": "GENERALISTA",
        "summary": "This is a DB test."
    }
    result = save_user_profile.invoke({"user_id": mock_id, "profile_dict": mock_profile})
    print(f"Result: {result}")
