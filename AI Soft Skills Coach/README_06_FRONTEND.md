# README 06 — Frontend: Templates, CSS, and JavaScript

---

## Architecture: Server-Rendered + AJAX Hybrid

This app uses a **hybrid approach**:

| What | How |
|------|-----|
| **Initial page load** | Server renders full HTML using Jinja2 templates |
| **Chat messages** | JavaScript fetches data via `fetch()` and updates the DOM dynamically |
| **Conversation switching** | JavaScript fetches conversation data and re-renders chat (no full page reload) |
| **Progress bars/scores** | JavaScript updates them live after each message |

This is sometimes called a **Mini-SPA** (Single Page Application) pattern.

---

## Template Hierarchy

```
dashboard_base.html  (master layout)
  ├── partials/topbar.html
  ├── partials/sidebar.html
  └── [block content]
       └── dashboard/chat.html   (main page content)
            └── dashboard/components/chat_message.html
```

---

## `dashboard_base.html` — The Master Layout

**File:** `src/templates/layouts/dashboard_base.html`

This is the outer shell for every dashboard page. It includes:
- CSS links (Bootstrap + all custom CSS files)
- The sidebar (via `{% include %}`)
- The topbar (via `{% include %}`)
- A `{% block content %}` placeholder where page-specific content goes
- Bootstrap JS and dashboard JS at the bottom

```html
<body class="dashboard-body">
    <div class="dashboard-shell">
        <!-- Left Sidebar -->
        <aside id="dashboardSidebar" class="dashboard-sidebar">
            {% include "partials/sidebar.html" %}
        </aside>

        <!-- Main Content Area -->
        <div class="dashboard-workspace">
            {% include "partials/topbar.html" %}
            <main class="dashboard-main-content">
                {% block content %}{% endblock %}  ← chat.html goes here
            </main>
        </div>
    </div>
</body>
```

---

## `sidebar.html` — Left Navigation Panel

**File:** `src/templates/partials/sidebar.html`

Contains:
- Navigation links (Chat, Conversations, Practice, Progress, etc.)
- Dynamically loaded conversation list (populated by JS)
- Daily Goal widget (from `daily_goal` context variable)
- Word of the Day widget (from `vocab` context variable)
- Weak Areas widget (from `weak_areas` context variable)
- Achievements/badges (from `badges` context variable)
- "New Conversation" button

```html
{% if daily_goal %}
<div class="sidebar-widget p-2 border rounded bg-white">
    <div class="d-flex justify-content-between align-items-center mb-1">
        <span class="fw-semibold"><i class="bi bi-bullseye text-primary"></i> Daily Goal</span>
        <span class="badge bg-primary">{{ daily_goal.percent }}%</span>
    </div>
    <div class="progress mb-1" style="height: 4px;">
        <div class="progress-bar bg-primary" style="width: {{ daily_goal.percent }}%;"></div>
    </div>
    <span class="text-muted">{{ daily_goal.current }}/{{ daily_goal.target }} mins today</span>
</div>
{% endif %}
```

---

## `chat.html` — The Main Dashboard Page

**File:** `src/templates/dashboard/chat.html`

This is the most complex template. It has three main sections:

### Left Column — Chat Panel

```html
<article class="surface-panel conversation-panel h-100">
    <!-- Header with conversation title and End Session button -->
    <div class="panel-header">
        <h1 class="panel-title mb-1">New Conversation</h1>
        <button id="endSessionButton">End Session</button>
    </div>

    <!-- Scrollable chat messages area -->
    <div id="chatMessages" class="chat-thread">
        {% for message in chat_messages %}
        {% include "dashboard/components/chat_message.html" %}
        {% endfor %}
    </div>

    <!-- Quick prompt buttons -->
    <div class="quick-prompt-row">
        {% for prompt in quick_prompts %}
        <button class="quick-prompt ripple-btn">
            <i class="bi bi-stars"></i>
            <span>{{ prompt }}</span>
        </button>
        {% endfor %}
    </div>

    <!-- Message input composer -->
    <div class="composer">
        <button class="composer-icon"><i class="bi bi-paperclip"></i></button>
        <input id="messageInput" class="composer-input" placeholder="Type your message...">
        <span id="voiceTimer" class="d-none">00:00</span>
        <button id="sendButton" class="composer-send"><i class="bi bi-send-fill"></i></button>
        <button id="recordButton" class="composer-voice"><i class="bi bi-mic-fill"></i></button>
    </div>
</article>
```

### Right Column — Progress and Feedback Panel

```html
<article class="surface-panel progress-panel">
    <!-- Circular progress ring -->
    <div class="progress-ring" data-score="{{ progress.overall }}">
        <span class="progress-ring-value">{{ progress.overall }}%</span>
    </div>

    <!-- Individual metric bars -->
    {% for metric in progress.metrics %}
    <div class="metric-item">
        <div class="metric-head">
            <span class="metric-label">
                <i class="bi {{ metric.icon }}"></i> {{ metric.label }}
            </span>
            <strong>{{ metric.score }}%</strong>
        </div>
        <div class="metric-track">
            <div class="metric-bar tone-{{ metric.tone }}" data-score="{{ metric.score }}"></div>
        </div>
    </div>
    {% endfor %}
</article>

<!-- Coach feedback card (hidden until first message) -->
<article id="coachAnalysisCard" class="surface-panel {% if not analysis %}d-none{% endif %}">
    <p id="analysisFeedback">{{ analysis.feedback }}</p>
    <ul id="analysisStrengths">...</ul>
    <ul id="analysisImprovements">...</ul>
    <ul id="grammarSuggestionsList">...</ul>
</article>
```

### Modals

Two modals in `chat.html`:
1. **Session Report Modal** (`#sessionReportModal`) — shown when "End Session" is clicked, displays scores + homework
2. **Settings Modal** (`#settingsModal`) — form to change native language and Groq API key

---

## Jinja2 Templating Syntax

| Syntax | Meaning |
|--------|---------|
| `{{ variable }}` | Print a variable value |
| `{% if condition %}...{% endif %}` | Conditional block |
| `{% for item in list %}...{% endfor %}` | Loop |
| `{% extends "base.html" %}` | Inherit from base template |
| `{% block name %}...{% endblock %}` | Define replaceable section |
| `{% include "file.html" %}` | Insert another template |
| `{{ url_for('static', path='css/x.css') }}` | Generate URL for static file |

---

## CSS Files

| File | Purpose |
|------|---------|
| `dashboard.css` | Base theme variables, layout grid, topbar, sidebar |
| `dashboard-modern.css` | Modern card styles, chat thread, scrollbars, fullscreen layout |
| `chat.css` | Mic recording animation, AI speaking indicator, speak button, toast |

### Key CSS Concepts Used

**CSS Variables (Custom Properties):**
```css
:root {
    --dashboard-primary: #6d5efc;
    --dashboard-bg: #f5f7ff;
    --dashboard-radius: 22px;
}
/* Used everywhere as: color: var(--dashboard-primary) */
```

**Dark Mode:**
```css
[data-theme="dark"] {
    --dashboard-bg: #0a1020;
    --dashboard-surface: rgba(15, 23, 42, 0.88);
}
```
When `data-theme="dark"` is set on `<html>`, the variables override to dark values. All colors update automatically.

**Conic Gradient for Progress Ring:**
```css
.progress-ring {
    --score: 0;
    background: conic-gradient(
        var(--dashboard-primary) 0 calc(var(--score) * 1%),
        rgba(109, 94, 252, 0.12) calc(var(--score) * 1%) 100%
    );
}
```
When JavaScript sets `ring.style.setProperty("--score", "82")`, the ring fills to 82%.

**Scrollable chat thread:**
```css
.chat-thread {
    flex: 1;
    min-height: 0;          /* critical — allows flex child to shrink */
    overflow-y: auto;
    scroll-behavior: smooth;
}
.chat-thread::-webkit-scrollbar { width: 6px; }
.chat-thread::-webkit-scrollbar-thumb {
    background: rgba(109, 94, 252, 0.35);
    border-radius: 999px;
}
```

**Mic recording animation:**
```css
.composer-voice.recording {
    background: #dc3545 !important;
    color: #fff !important;
    animation: pulse-red 1s ease infinite;
}
@keyframes pulse-red {
    0%,100% { box-shadow: 0 0 0 4px rgba(220,53,69,.25); }
    50%      { box-shadow: 0 0 0 8px rgba(220,53,69,.05); }
}
```

---

## JavaScript Files

### `dashboard.js` — UI Utilities

| Function | What it does |
|----------|-------------|
| Sidebar toggle | Opens/closes sidebar on mobile when hamburger is clicked |
| Theme toggle | Switches between light/dark mode, saves to `localStorage` |
| Ripple effect | Creates ripple animation on button clicks |
| Progress rings | Sets `--score` CSS variable for the ring gradient on page load |

```javascript
// Theme toggle
const themeToggle = document.getElementById("themeToggle");
themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    localStorage.setItem("speakai-theme", next);
    document.documentElement.setAttribute("data-theme", next);
    themeToggle.innerHTML = next === "dark" ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
});

// Restore saved theme on page load
const savedTheme = localStorage.getItem("speakai-theme");
if (savedTheme) {
    document.documentElement.setAttribute("data-theme", savedTheme);
}
```

### `chat.js` — All Chat Interactions

This is the largest and most important JS file. Key functions:

| Function | Lines of code | What it does |
|----------|--------------|-------------|
| `sendMessage(text)` | ~30 | Sends text to `/dashboard/message`, renders response |
| `sendAudioMessage(blob)` | ~30 | Uploads audio blob, renders transcribed response |
| `playAiAudio(url)` | ~25 | Plays MP3, handles autoplay block |
| `recordButton listener` | ~40 | Starts/stops MediaRecorder, handles permissions |
| `updateDashboardStats(scores)` | ~25 | Updates all progress bars and ring |
| `updateCoachAnalysis(data)` | ~35 | Updates feedback/strengths/improvements/grammar cards |
| `loadSidebarConversations()` | ~40 | Fetches and renders conversation list in sidebar |
| `loadConversation(id)` | ~35 | Loads a past conversation's messages |
| `endSessionButton listener` | ~50 | Ends session, populates and shows report modal |
| `settingsForm listener` | ~20 | Saves settings, reloads page |

---

## How the Sidebar Conversation List Works

On every page load, JavaScript fetches all conversations:

```javascript
const loadSidebarConversations = async () => {
    const response = await fetch("/conversations");   // → ConversationService.get_user_conversations()
    const conversations = await response.json();

    conversations.forEach(conv => {
        listContainer.insertAdjacentHTML("beforeend", `
            <a href="/conversation/${conv.id}" class="conversation-card ...">
                <strong>${escapeHtml(conv.topic)}</strong>
                <span class="badge ${badgeColor}">${badgeText}</span>
                <div class="text-muted">${formatDate(conv.created_at)}</div>
            </a>`);
    });
};
```

When a conversation card is clicked:
```javascript
listContainer.addEventListener("click", async (e) => {
    const card = e.target.closest(".conversation-card");
    if (!card) return;
    e.preventDefault();  // ← prevents full page reload

    const convId = card.getAttribute("href").split("/").pop();
    history.pushState({ conversationId: convId }, "", `/conversation/${convId}`);
    // ↑ Updates the browser URL bar without reloading

    await loadConversation(convId);  // fetches and renders messages
});
```

---

## Bootstrap 5 Components Used

| Component | Where |
|-----------|-------|
| Grid system (`.row`, `.col-*`) | Two-column layout |
| Cards (`.card`) | Panel containers |
| Progress bars | Metric bars |
| Modals | Session report, settings |
| Badges | Conversation status, daily goal % |
| Buttons | All interactive buttons |
| Spinners | Loading indicators |
| `d-none` / `d-flex` | Show/hide elements |
| Bootstrap Icons (`bi-*`) | All icons throughout the app |

---

## Static File Serving

**File:** `main.py`

```python
app.mount("/static", StaticFiles(directory="src/static"), name="static")
```

This makes everything in `src/static/` accessible at `/static/...`:
- `src/static/css/dashboard.css` → `/static/css/dashboard.css`
- `src/static/audio/reply_abc.mp3` → `/static/audio/reply_abc.mp3`
- `src/static/audio/uploads/user_xyz.webm` → `/static/audio/uploads/user_xyz.webm`
