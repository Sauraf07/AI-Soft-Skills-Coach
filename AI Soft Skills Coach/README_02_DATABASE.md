# README 02 — Database: All 9 Tables Explained

The database is **MySQL** named `ai_softskill`. SQLAlchemy talks to it using the async driver `aiomysql`. Alembic manages all schema changes.

---

## Database Connection

**File:** `src/db/db_config.py`

```python
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

load_dotenv()
URL = os.getenv("DATABASE_URL", "mysql+aiomysql://root:root@localhost:3306/ai_softskill")

engine = create_async_engine(URL, echo=False)
Sessionlocal = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass
```

- `create_async_engine` — creates a non-blocking connection pool to MySQL
- `async_sessionmaker` — factory that produces async database sessions
- `Base` — parent class for all SQLAlchemy models
- `expire_on_commit=False` — objects stay usable after a commit (important for async)

**How sessions are used in routes:**
```python
async with Sessionlocal() as session:
    # do database operations
    await session.commit()
# session auto-closes here
```

---

## The 9 Database Tables

### Table Relationships (Overview)

```
user (1)
  ├──< conversations (many)
  │       └──< messages (many)
  │       └── analysis (one)
  ├── user_progress (one)
  ├──< learning_goals (many)
  ├──< vocabulary_words (many)
  │       └──< vocabulary_progress (many)
  └──< achievements (many)
```

---

### Table 1: `user`

**File:** `src/models/user.py`

Stores every registered user.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | Auto-increment |
| `username` | VARCHAR(100) | Display name |
| `email` | VARCHAR(100) UNIQUE | Login email |
| `password` | VARCHAR(255) | bcrypt hash (NOT plain text) |
| `profile_image` | VARCHAR(255) | File path (currently unused) |
| `native_language` | VARCHAR(100) | e.g. "Hindi", "English" |
| `created_at` | DATETIME | When they registered |
| `updated_at` | DATETIME | Last update |

```python
class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    ...
    # Relationships — SQLAlchemy can auto-fetch related records
    conversations = relationship("Conversation", back_populates="user")
    progress = relationship("UserProgress", back_populates="user", uselist=False)
    learning_goals = relationship("LearningGoal", back_populates="user")
    vocabulary_words = relationship("VocabularyWord", back_populates="user")
    achievements = relationship("Achievement", back_populates="user")
```

---

### Table 2: `conversations`

**File:** `src/models/conversation.py`

Each time a user starts a new chat session, one row is created here.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | Auto-increment |
| `user_id` | INT FK → user.id | Who owns this conversation |
| `topic` | VARCHAR(150) | Auto-set to first 30 chars of first message |
| `start_time` | DATETIME | When conversation started |
| `end_time` | DATETIME (nullable) | Set when "End Session" is clicked |
| `duration_seconds` | INT (nullable) | end_time - start_time in seconds |
| `status` | ENUM | `"in_progress"` or `"completed"` |
| `created_at` | DATETIME | Row creation time |

```python
status: Mapped[str] = mapped_column(
    Enum("completed", "in_progress", name="conversation_status"),
    server_default="completed"
)
```

**Key business logic:**
- Only one conversation can be `"in_progress"` at a time per user
- When "New Conversation" is clicked, the current in-progress one is set to `"completed"` first
- Topic starts as "New Conversation" and is renamed to the user's first message

---

### Table 3: `messages`

**File:** `src/models/message.py`

Every single message sent by user or AI is stored here.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | Auto-increment |
| `conversation_id` | INT FK → conversations.id | Which conversation |
| `sender` | ENUM | `"user"` or `"ai"` |
| `message_text` | TEXT | The actual message content |
| `message_type` | ENUM | `"text"` or `"audio"` |
| `audio_url` | VARCHAR(255) (nullable) | Path to .webm file for voice messages |
| `created_at` | DATETIME | Timestamp |

```python
sender: Mapped[str] = mapped_column(
    Enum("user", "ai", name="message_sender"), nullable=False
)
```

**Note:** Audio messages have `message_type="audio"` and `audio_url` points to the saved `.webm` file. But `message_text` still contains the **transcribed text** from Whisper — so the AI can read it.

---

### Table 4: `analyses`

**File:** `src/models/analysis.py`

One analysis record per conversation. Updated on every message exchange.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | |
| `conversation_id` | INT FK UNIQUE | One analysis per conversation |
| `grammar_score` | DECIMAL(5,2) | 0.00 – 100.00 |
| `vocabulary_score` | DECIMAL(5,2) | |
| `confidence_score` | DECIMAL(5,2) | |
| `fluency_score` | DECIMAL(5,2) | |
| `pronunciation_score` | DECIMAL(5,2) | Defaults to 80 for text (no actual audio analysis) |
| `overall_score` | DECIMAL(5,2) | Weighted average |
| `feedback` | TEXT | Short coaching paragraph |
| `strengths` | TEXT | Comma-separated list e.g. "Clear greeting, Good tone" |
| `improvements` | TEXT | Comma-separated list e.g. "Past Tense, Prepositions" |
| `created_at` | DATETIME | |

```python
conversation_id: Mapped[int] = mapped_column(
    ForeignKey("conversations.id"), nullable=False, unique=True
)
```

The `unique=True` on `conversation_id` means there is **exactly one** analysis per conversation — it gets updated, not duplicated.

---

### Table 5: `user_progress`

**File:** `src/models/user_progress.py`

Lifetime statistics for each user. One row per user.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | |
| `user_id` | INT FK UNIQUE | One row per user |
| `total_conversations` | INT | Count of all conversations ever |
| `total_minutes` | INT | Estimated total speaking time (adds 2 per message) |
| `average_score` | DECIMAL(5,2) | Rolling average across all analyses |
| `current_streak` | INT | Consecutive days practiced (simplified) |
| `longest_streak` | INT | Best streak ever |
| `last_conversation_at` | DATETIME | When they last practiced |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

**Updated on every message:**
```python
progress.total_conversations = total_convs
progress.average_score = avg_score
progress.total_minutes += 2  # adds 2 minutes per message exchange
progress.last_conversation_at = datetime.now()
```

---

### Table 6: `learning_goals`

**File:** `src/models/learning_goal.py`

Goals set for the user. Currently auto-created with a default "Practice Speaking — 10 minutes" goal.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | |
| `user_id` | INT FK | |
| `title` | VARCHAR(150) | e.g. "Practice Speaking" |
| `description` | TEXT | e.g. "Speak for 10 minutes" |
| `target_score` | INT | Target in minutes (10 = 10 minutes/day) |
| `start_date` | DATE | |
| `end_date` | DATE (nullable) | |
| `status` | ENUM | `"active"`, `"completed"`, `"paused"` |
| `created_at` | DATETIME | |

**How the daily goal progress is calculated:**
```python
# Count user messages sent today
user_msg_count = count of messages where sender="user" AND created_at >= today midnight
minutes_today = min(10.0, float(user_msg_count))   # 1 message ≈ 1 minute
goal_percent = int((minutes_today / 10) * 100)
```

---

### Table 7: `vocabulary_words`

**File:** `src/models/vocabulary_word.py`

Words assigned to the user for learning. Shown in the sidebar as "Word of the Day".

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | |
| `user_id` | INT FK | |
| `word` | VARCHAR(100) | e.g. "Enthusiastic" |
| `meaning` | TEXT | e.g. "Very excited and interested." |
| `example` | TEXT | e.g. "I am enthusiastic about learning." |
| `created_at` | DATETIME | |

Default word auto-created if none exists: "Enthusiastic".

---

### Table 8: `vocabulary_progress`

**File:** `src/models/vocabulary_progress.py`

Tracks how well the user knows each vocabulary word.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | |
| `word_id` | INT FK → vocabulary_words.id | |
| `user_id` | INT FK → user.id | |
| `status` | ENUM | `"new"`, `"learning"`, `"known"` |
| `review_count` | INT | How many times reviewed |
| `last_reviewed_at` | DATETIME (nullable) | |

Currently defined in schema but not actively used in the UI — ready for a future spaced repetition feature.

---

### Table 9: `achievements`

**File:** `src/models/achievement.py`

Badges earned by the user. Auto-awarded when conversation milestones are hit.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK | |
| `user_id` | INT FK | |
| `title` | VARCHAR(150) | e.g. "First Talk" |
| `description` | TEXT | e.g. "Start 1 conversation" |
| `icon` | VARCHAR(255) | Emoji e.g. "🏅" |
| `earned_at` | DATETIME | When badge was awarded |

**Auto-award logic** in `DashboardService.build_context()`:
```python
available_badges = [
    {"title": "First Talk",           "icon": "🏅", "req_conv": 1},
    {"title": "Speech Explorer",      "icon": "🚀", "req_conv": 5},
    {"title": "Communication Master", "icon": "🏆", "req_conv": 10},
]

for badge in available_badges:
    is_earned = badge["title"] in earned_ach_titles
    if not is_earned and total_convs >= badge["req_conv"]:
        # Create the achievement row
        self.session.add(Achievement(user_id=user.id, title=badge["title"], ...))
        is_earned = True
```

---

## Repository Layer (How Queries Are Written)

**File:** `src/repository/base_repo.py`

All repositories inherit from `BaseRepository` which provides standard operations:

```python
class BaseRepository(Generic[ModelType]):

    async def create(self, obj):
        self.session.add(obj)
        await self.session.flush()    # sends SQL INSERT, but doesn't commit yet
        await self.session.refresh(obj)  # loads generated ID back
        return obj

    async def get_by_id(self, obj_id):
        return await self.session.get(self.model, obj_id)

    async def get_one_by(self, **filters):
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return result.scalar_one_or_none()   # None if not found, raises if >1

    async def update_by_id(self, obj_id, data: dict):
        obj = await self.get_by_id(obj_id)
        for key, value in data.items():
            setattr(obj, key, value)   # set each field
        await self.session.flush()
        return obj

    async def delete_by_id(self, obj_id):
        obj = await self.get_by_id(obj_id)
        await self.session.delete(obj)
        await self.session.flush()
        return True
```

**Difference between `flush()` and `commit()`:**
- `flush()` — sends the SQL to the database but keeps it in a transaction (can be rolled back)
- `commit()` — permanently saves everything to disk

**Custom repository example** — `ConversationRepository`:
```python
class ConversationRepository(BaseRepository[Conversation]):

    async def get_recent_by_user(self, user_id: int, limit: int = 3):
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_by_user(self, user_id: int):
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
```
