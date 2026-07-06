# README 03 — Authentication System

This project uses **session-based authentication** (like traditional websites), not JWT tokens. Here is everything about how users are registered, logged in, protected, and logged out.

---

## Overview

```
Register → Hash password → Save to DB → Redirect to Login
Login    → Verify password → Store user_id in cookie → Redirect to Dashboard
Every Request → Middleware reads cookie → Loads user from DB → Attaches to request
Logout   → Clear cookie → Redirect to Login
```

---

## 1. Password Security

**File:** `src/utils/password.py`

```python
import bcrypt

def hash_password(password: str):
    password_bytes = password.encode('utf-8')
    salt_key = bcrypt.gensalt(12)         # work factor 12 (takes ~0.3 seconds)
    return bcrypt.hashpw(password_bytes, salt_key).decode('utf-8')

def verify_password(password: str, hash_password: str):
    password_bytes = password.encode('utf-8')
    hash_bytes = hash_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)
```

### How bcrypt works:
- `"hello123"` → `"$2b$12$randomsalt...hashedvalue"` (60 characters)
- The `$12$` means it runs 2^12 = 4,096 internal iterations — slow on purpose
- Two hashes of the same password are **always different** (random salt)
- You can NEVER reverse a bcrypt hash back to the original password
- `verify_password` works by hashing the input again with the same salt and comparing

---

## 2. Registration

**File:** `src/routes/auth.py` + `src/services/user_service.py`

```python
# Route handler
@router.post("/register")
async def register_submit(request, username, email, password, native_language):
    async with Sessionlocal() as session:
        user_service = UserService(session)
        user = User(username=username, email=email, password=password, native_language=native_language)
        try:
            user = await user_service.register_user(user)
        except ValueError as exc:
            return login page with error message

    return RedirectResponse(url="/login?message=Success...", status_code=303)

# Service layer
async def register_user(self, user: User):
    # 1. Check email uniqueness
    existing = await self.user_repo.get_user_by_email(user.email)
    if existing:
        raise ValueError("An account with this email already exists.")

    # 2. Hash the password (replaces plain text)
    user.password = hash_password(user.password)

    # 3. Save to database
    created_user = await self.user_repo.create_user(user)

    # 4. Create blank UserProgress row for this user
    await self.user_progress_repo.ensure_default_for_user(created_user.id)

    # 5. Commit everything
    await self.session.commit()
    return created_user
```

---

## 3. Login

**File:** `src/routes/auth.py` + `src/services/user_service.py`

```python
# Route handler
@router.post("/login")
async def login_submit(request, email, password):
    async with Sessionlocal() as session:
        user_service = UserService(session)
        user = await user_service.authenticate_user(email=email, password=password)
        if not user:
            return login page with error "Invalid email or password"
        start_user_session(request.session, user)
    return RedirectResponse(url="/dashboard", status_code=303)

# Service layer
async def authenticate_user(self, email: str, password: str):
    user = await self.user_repo.get_user_by_email(email)
    if not user:
        return None    # email not found
    if not verify_password(password, user.password):
        return None    # wrong password
    return user        # success
```

**Important:** Both "email not found" and "wrong password" return the same error message. This prevents attackers from knowing which emails are registered.

---

## 4. Sessions (The Cookie)

**File:** `src/utils/session.py`

```python
SESSION_IS_LOGGED_IN = "is_logged_in"
SESSION_USER_ID = "user_id"
SESSION_USER_EMAIL = "user_email"
SESSION_USER_NAME = "user_name"

def start_user_session(session: dict, user: User):
    session["is_logged_in"] = True
    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.username

def clear_user_session(session: dict):
    for key in ("is_logged_in", "user_id", "user_email", "user_name"):
        session.pop(key, None)
```

**How sessions work in Starlette:**
1. `app.add_middleware(SessionMiddleware, secret_key="...")` — registered in `main.py`
2. When `session["user_id"] = 5` is set, Starlette serializes this dict, **encrypts it** using the `SESSION_SECRET_KEY`, and sends it to the browser as a cookie called `session`
3. On every request, the browser sends this cookie back
4. Starlette decrypts it and makes it available as `request.session`
5. The data is only readable by the server — the user sees a scrambled string

**Why store `user_id` and not the full user object?**
Because the user object might change (email update, etc.) and we need the latest from the database. The middleware re-fetches the full user on every request using the stored ID.

---

## 5. Auth Middleware — The Guard

**File:** `src/middleware/auth.py`

This runs **before every single route handler** in the entire app.

```python
class Auth(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_urls = {"/", "/login", "/register", "/logout", "/docs", "/openapi.json", "/redoc"}

        # RULE 1: Static files (CSS, JS, images) pass through freely
        if request.url.path.startswith("/static"):
            return await call_next(request)

        # RULE 2: Public pages pass through freely
        if request.url.path in public_urls:
            return await call_next(request)

        # RULE 3: Protected pages — check login
        if not request.session.get("is_logged_in"):
            return RedirectResponse("/login", status_code=303)

        # RULE 4: Get user_id from session
        user_id = request.session.get("user_id")
        if user_id is None:
            clear_user_session(request.session)
            return RedirectResponse("/login", status_code=303)

        # RULE 5: Load user from DB — verify they still exist
        async with Sessionlocal() as session:
            user_service = UserService(session)
            current_user = await user_service.get_user_by_id(user_id)

        # RULE 6: If user was deleted, log them out
        if current_user is None:
            clear_user_session(request.session)
            return RedirectResponse("/login", status_code=303)

        # RULE 7: Attach user to request for use in handlers
        request.state.current_user = current_user
        return await call_next(request)   # ← continue to the actual route
```

**Accessing the user in any route:**
```python
user = getattr(request.state, "current_user", None)
if not user:
    return {"error": "Not authenticated"}
```

---

## 6. Logout

**File:** `src/routes/auth.py`

```python
@router.get("/logout")
async def logout(request: Request):
    clear_user_session(request.session)    # wipes all session keys
    return RedirectResponse(url="/login", status_code=303)
```

The cookie data is cleared. The encrypted cookie in the browser now decrypts to an empty dict, so `session.get("is_logged_in")` returns `None` → middleware redirects to login.

---

## 7. User Profile Levels

**File:** `src/utils/session.py` → `build_profile()`

```python
def build_profile(user: User, progress: UserProgress | None = None):
    score = float(progress.average_score) if progress else 0.0

    if score >= 80:
        level = "Advanced"
    elif score >= 50:
        level = "Intermediate"
    else:
        level = "Beginner"

    # Build initials: "Saurav Kumar" → "SK"
    initials = "".join(part[0] for part in user.username.split()[:2]).upper()

    return {
        "id": user.id,
        "name": user.username,
        "email": user.email,
        "level": level,         # shown in topbar
        "initials": initials,   # shown in avatar circle
        "native_language": user.native_language,
        "score": score,
    }
```

This profile dict is included in the dashboard template context and rendered in the topbar as "Saurav Kumar — Advanced".

---

## 8. Settings — Changing Native Language / API Key

**File:** `src/routes/dashboard.py`

```python
@router.post("/dashboard/settings")
async def save_settings(request, native_language, groq_api_key):
    user = request.state.current_user

    # Update native_language in database
    async with Sessionlocal() as session:
        db_user = await session.get(User, user.id)
        db_user.native_language = native_language
        await session.commit()

    # Update GROQ key in memory AND in .env file
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key.strip()

        # Rewrite .env file so key persists after server restart
        with open(".env", "r") as f:
            content = f.readlines()
        for idx, line in enumerate(content):
            if line.startswith("GROQ_API_KEY="):
                content[idx] = f"GROQ_API_KEY={groq_api_key.strip()}\n"
                break
        with open(".env", "w") as f:
            f.writelines(content)

    return {"success": True}
```

The `LLMService` calls `load_dotenv(override=True)` on every instantiation, so the new key is picked up immediately without restarting the server.
