"""
Admin Service — Administration Panel Business Logic
=====================================================
Functions for course management, competencies, users,
roadmaps and admin panel metrics.
Currently uses stub data in memory; will connect to PostgreSQL
in production.

TODO:
  - Replace *_DB dicts with queries to corresponding tables
  - Integrate with the RAG indexer for course re-indexing
"""

import uuid

# ──────────────────────────────────────────────
# STUB DATABASES (in-memory)
# ──────────────────────────────────────────────
COURSES_DB: dict[str, dict] = {
    "course-python-101": {
        "id": "course-python-101",
        "title": "Python for Beginners",
        "description": "Introductory Python course for data science",
        "level": "beginner",
        "affinity": "both",
        "competencies": ["comp-python"],
        "duration_hours": 40,
        "url": "https://example.com/python-101",
    },
    "course-ml-201": {
        "id": "course-ml-201",
        "title": "Introduction to Machine Learning",
        "description": "ML fundamentals with scikit-learn",
        "level": "intermediate",
        "affinity": "specialist",
        "competencies": ["comp-ml", "comp-python"],
        "duration_hours": 60,
        "url": "https://example.com/ml-201",
    },
}

COMPETENCIES_DB: dict[str, dict] = {
    "comp-python": {
        "id": "comp-python",
        "name": "Python Programming",
        "description": "Mastery of the Python language and its ecosystem",
    },
    "comp-ml": {
        "id": "comp-ml",
        "name": "Machine Learning",
        "description": "Fundamentals and application of ML algorithms",
    },
    "comp-data": {
        "id": "comp-data",
        "name": "Data Analysis",
        "description": "Ability to explore, clean and analyze datasets",
    },
}

USERS_DB: dict[str, dict] = {}
ROADMAPS_DB: dict[str, dict] = {}


# ──────────────────────────────────────────────
# COURSES — CRUD
# ──────────────────────────────────────────────


def list_courses(level: str | None = None, affinity: str | None = None) -> list[dict]:
    """List courses with optional filters by level and affinity."""
    courses = list(COURSES_DB.values())
    if level:
        courses = [c for c in courses if c["level"] == level]
    if affinity:
        courses = [c for c in courses if c["affinity"] == affinity]
    return courses


def get_course(course_id: str) -> dict | None:
    """Get a course by its ID."""
    return COURSES_DB.get(course_id)


def create_course(data: dict) -> dict:
    """Create a new course."""
    course_id = f"course-{uuid.uuid4().hex[:8]}"
    course = {"id": course_id, **data}
    COURSES_DB[course_id] = course
    return course


def update_course(course_id: str, updates: dict) -> dict | None:
    """Update fields of an existing course."""
    course = COURSES_DB.get(course_id)
    if not course:
        return None
    course.update(updates)
    return course


def delete_course(course_id: str) -> bool:
    """Delete a course. Returns True if it existed."""
    return COURSES_DB.pop(course_id, None) is not None


# ──────────────────────────────────────────────
# COMPETENCIES — Read-only
# ──────────────────────────────────────────────


def list_competencies() -> list[dict]:
    """List all competencies in the taxonomy."""
    return list(COMPETENCIES_DB.values())


def get_competency(comp_id: str) -> dict | None:
    """Get a competency by its ID."""
    return COMPETENCIES_DB.get(comp_id)


# ──────────────────────────────────────────────
# USERS — Stubs
# ──────────────────────────────────────────────


def list_users(page: int = 1, page_size: int = 20) -> dict:
    """List users with pagination."""
    users = list(USERS_DB.values())
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": users[start:end],
        "total": len(users),
        "page": page,
        "page_size": page_size,
    }


def get_user(user_id: str) -> dict | None:
    """Get a user by their ID."""
    return USERS_DB.get(user_id)


def toggle_user_status(user_id: str, is_active: bool) -> bool:
    """Activate or deactivate a user."""
    user = USERS_DB.get(user_id)
    if not user:
        return False
    user["is_active"] = is_active
    return True


# ──────────────────────────────────────────────
# ROADMAPS — Stubs
# ──────────────────────────────────────────────


def list_roadmaps(
    approach: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """List roadmaps with filters."""
    roadmaps = list(ROADMAPS_DB.values())
    if approach:
        roadmaps = [r for r in roadmaps if r.get("approach") == approach]
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": roadmaps[start:end],
        "total": len(roadmaps),
        "page": page,
        "page_size": page_size,
    }


def get_roadmap(roadmap_id: str) -> dict | None:
    """Get a roadmap by its ID."""
    return ROADMAPS_DB.get(roadmap_id)


def add_block_to_roadmap(
    roadmap_id: str, phase_order: int, content_id: str, position: int | None = None
) -> bool:
    """Add a block to a phase of a roadmap."""
    roadmap = ROADMAPS_DB.get(roadmap_id)
    if not roadmap:
        return False
    for phase in roadmap.get("phases", []):
        if phase["phase_order"] == phase_order:
            block = {
                "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                "content_id": content_id,
                "title": f"Course {content_id}",
                "order": position or len(phase["blocks"]) + 1,
                "completed": False,
            }
            phase["blocks"].append(block)
            return True
    return False


def remove_block_from_roadmap(
    roadmap_id: str, phase_order: int, content_id: str
) -> bool:
    """Remove a block from a phase of a roadmap."""
    roadmap = ROADMAPS_DB.get(roadmap_id)
    if not roadmap:
        return False
    for phase in roadmap.get("phases", []):
        if phase["phase_order"] == phase_order:
            original_len = len(phase["blocks"])
            phase["blocks"] = [
                b for b in phase["blocks"] if b["content_id"] != content_id
            ]
            return len(phase["blocks"]) < original_len
    return False


# ──────────────────────────────────────────────
# METRICS
# ──────────────────────────────────────────────


def get_admin_metrics() -> dict:
    """Return aggregated metrics for the admin panel."""
    total_users = len(USERS_DB)
    active_users = sum(1 for u in USERS_DB.values() if u.get("is_active", True))
    total_roadmaps = len(ROADMAPS_DB)

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_roadmaps": total_roadmaps,
        "total_courses": len(COURSES_DB),
        "trajectory_distribution": {"generalist": 0, "specialist": 0},
        "top_courses": [],
    }
