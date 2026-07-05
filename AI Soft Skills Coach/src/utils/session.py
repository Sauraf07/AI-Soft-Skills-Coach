from __future__ import annotations

from src.models.user import User
from src.models.user_progress import UserProgress

SESSION_IS_LOGGED_IN = "is_logged_in"
SESSION_USER_ID = "user_id"
SESSION_USER_EMAIL = "user_email"
SESSION_USER_NAME = "user_name"


def start_user_session(session: dict, user: User):
    session[SESSION_IS_LOGGED_IN] = True
    session[SESSION_USER_ID] = user.id
    session[SESSION_USER_EMAIL] = user.email
    session[SESSION_USER_NAME] = user.username


def clear_user_session(session: dict):
    for key in (
        SESSION_IS_LOGGED_IN,
        SESSION_USER_ID,
        SESSION_USER_EMAIL,
        SESSION_USER_NAME,
    ):
        session.pop(key, None)


def build_profile(user: User, progress: UserProgress | None = None):
    score = (
        float(progress.average_score)
        if progress and progress.average_score is not None
        else 0.0
    )

    if score >= 80:
        level = "Advanced"
    elif score >= 50:
        level = "Intermediate"
    else:
        level = "Beginner"

    initials = "".join(part[0] for part in user.username.split()[:2]).upper()
    if not initials:
        initials = user.username[:2].upper() or "U"

    return {
        "id": user.id,
        "name": user.username,
        "email": user.email,
        "level": level,
        "initials": initials,
        "native_language": user.native_language,
        "score": score,
    }
