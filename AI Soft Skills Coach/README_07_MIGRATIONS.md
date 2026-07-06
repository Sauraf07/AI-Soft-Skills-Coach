# README 07 — Alembic Migrations: Database Version Control

Alembic is the tool that manages all changes to the database schema. Instead of manually writing `CREATE TABLE` SQL, you define Python models and Alembic generates the SQL automatically.

---

## What is a Migration?

A migration file is a Python script with two functions:
- `upgrade()` — applies the change (e.g., creates a table)
- `downgrade()` — reverses the change (e.g., drops a table)

Each migration has a unique **revision ID** (like a git commit hash).

---

## How to Use Alembic

### Apply all pending migrations (create/update tables):
```bash
alembic upgrade head
```
`head` means "apply all migrations up to the latest one".

### Create a new migration after changing a model:
```bash
alembic revision --autogenerate -m "describe your change here"
```
Alembic compares your Python models with the current database and generates the diff.

### Roll back one migration:
```bash
alembic downgrade -1
```

### See migration history:
```bash
alembic history
```

### See current version:
```bash
alembic current
```

---

## Configuration

**File:** `alembic.ini`

The key setting is the database URL:
```ini
sqlalchemy.url = mysql+pymysql://root:root@localhost:3306/ai_softskill
```

**Important:** `alembic.ini` uses the **synchronous** PyMySQL driver, even though the main app uses the async `aiomysql` driver. Alembic runs migrations synchronously.

---

## `alembic/env.py` — The Migration Runner

```python
from src.db.db_config import Base
import src.models   # ← IMPORTANT: imports all models so Alembic knows about them

target_metadata = Base.metadata   # Alembic compares against these models

async def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

asyncio.run(run_migrations_online())
```

The `import src.models` line is critical — if a model is not imported here, Alembic won't know it exists and won't generate migrations for it.

---

## All 13 Migration Files

Listed in chronological order (oldest to newest):

### 1. `f630f755f421` — User Model Added
Creates the `user` table.
```python
op.create_table('user',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('username', sa.String(100)),
    sa.Column('email', sa.String(100), unique=True),
    sa.Column('password', sa.String(100)),
    sa.Column('profile_image', sa.String(100)),
    sa.Column('native_language', sa.String(100)),
    sa.Column('created_at', sa.DateTime()),
    sa.Column('updated_at', sa.DateTime()),
)
```

### 2. `5705addfbcbc` — Conversation Model Added
Creates the `conversations` table with `user_id` foreign key.

### 3. `7b4012355d2a` — Message Model Added
Creates the `messages` table with `conversation_id` foreign key and the `sender`/`message_type` ENUM columns.

### 4. `337dc61bb930` — Analysis Model Added
Creates the `analyses` table with all score columns (DECIMAL type).

### 5. `b6a7c52d487c` — User Progress Model Added
Creates `user_progress` with stats columns.

### 6. `5e20e0e2d5e6` — Vocab Model Added
Creates `vocabulary_words` table.

### 7. `3fc05db1acd8` — Vocab Progress Model Added
Creates `vocabulary_progress` linking users to words.

### 8. `af33e1fdae4f` — Learning Goal Model Added
Creates `learning_goals` table.

### 9. `42b93d1b3f07` — Achievements Model Added
Creates `achievements` table.

### 10. `36ae4d4c8a5c` — User Model Updated
Adds or modifies columns on the `user` table (e.g. increased password length to 255).

### 11. `d0b9a797575c` — User Model Updated (again)
Further adjustments to user table columns.

### 12. `bdf40e64bf48` — Models Added/Updated
Batch update to multiple models.

### 13. `ceae118eaec1` — Models Added/Updated (latest)
Most recent migration — current state of the database.

---

## The Migration Chain

Each migration references the previous one via `down_revision`:

```python
# Migration 1 (first ever)
revision = 'f630f755f421'
down_revision = None          # ← no parent

# Migration 2
revision = '5705addfbcbc'
down_revision = 'f630f755f421'  # ← parent is migration 1

# Migration 3
revision = '7b4012355d2a'
down_revision = '5705addfbcbc'  # ← parent is migration 2
```

This forms a chain. `alembic upgrade head` runs all of them in order from first to last.

---

## Complete Database Schema (Final State)

After running `alembic upgrade head`, these tables exist:

```sql
-- user
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    profile_image VARCHAR(255) NOT NULL DEFAULT '',
    native_language VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- conversations
CREATE TABLE conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    topic VARCHAR(150) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_seconds INT,
    status ENUM('completed', 'in_progress') NOT NULL DEFAULT 'completed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- messages
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    sender ENUM('user', 'ai') NOT NULL,
    message_text TEXT NOT NULL,
    message_type ENUM('text', 'audio') NOT NULL DEFAULT 'text',
    audio_url VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- analyses (one per conversation)
CREATE TABLE analyses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL UNIQUE,
    grammar_score DECIMAL(5,2),
    vocabulary_score DECIMAL(5,2),
    confidence_score DECIMAL(5,2),
    fluency_score DECIMAL(5,2),
    pronunciation_score DECIMAL(5,2),
    overall_score DECIMAL(5,2),
    feedback TEXT,
    strengths TEXT,
    improvements TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- user_progress (one per user)
CREATE TABLE user_progress (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    total_conversations INT NOT NULL DEFAULT 0,
    total_minutes INT NOT NULL DEFAULT 0,
    average_score DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    last_conversation_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- learning_goals
CREATE TABLE learning_goals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    target_score INT,
    start_date DATE NOT NULL,
    end_date DATE,
    status ENUM('active', 'completed', 'paused') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- vocabulary_words
CREATE TABLE vocabulary_words (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    word VARCHAR(100) NOT NULL,
    meaning TEXT,
    example TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- vocabulary_progress
CREATE TABLE vocabulary_progress (
    id INT PRIMARY KEY AUTO_INCREMENT,
    word_id INT NOT NULL,
    user_id INT NOT NULL,
    status ENUM('new', 'learning', 'known') NOT NULL DEFAULT 'new',
    review_count INT NOT NULL DEFAULT 0,
    last_reviewed_at DATETIME,
    FOREIGN KEY (word_id) REFERENCES vocabulary_words(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- achievements
CREATE TABLE achievements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    icon VARCHAR(255),
    earned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

---

## Adding a New Column (Example Workflow)

Say you want to add a `phone_number` column to `user`:

**Step 1:** Edit `src/models/user.py`:
```python
phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
```

**Step 2:** Generate the migration:
```bash
alembic revision --autogenerate -m "add phone_number to user"
```

**Step 3:** Apply it:
```bash
alembic upgrade head
```

Alembic generates:
```python
def upgrade():
    op.add_column('user', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('user', 'phone_number')
```
