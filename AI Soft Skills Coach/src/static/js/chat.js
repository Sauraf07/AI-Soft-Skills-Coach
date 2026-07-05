/* ========================
   Chat & Audio Interaction
   ======================== */

document.addEventListener("DOMContentLoaded", () => {
  const chatContainer = document.getElementById("chatMessages");
  const messageInput = document.getElementById("messageInput");
  const sendButton = document.getElementById("sendButton");
  const recordButton = document.getElementById("recordButton");
  const voiceTimer = document.getElementById("voiceTimer");

  // Auto scroll chat to bottom
  const scrollToBottom = () => {
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  };
  scrollToBottom();

  // Parse and set conic-gradient for progress rings
  const updateProgressRings = () => {
    document.querySelectorAll(".progress-ring[data-score]").forEach((ring) => {
      const score = Number(ring.dataset.score || 0);
      ring.style.setProperty("--score", String(score));
      const value = ring.querySelector(".progress-ring-value");
      if (value) {
        value.textContent = `${score}%`;
      }
    });

    document.querySelectorAll(".metric-bar[data-score]").forEach((bar) => {
      const score = Number(bar.dataset.score || 0);
      bar.style.width = `${score}%`;
      
      // Update the badge score if it exists
      const head = bar.closest(".metric-item")?.querySelector("strong");
      if (head) {
        head.textContent = `${score}%`;
      }
    });
  };
  updateProgressRings();

  // HTML template builders
  const buildUserBubble = (text, time) => {
    return `
      <div class="chat-row user-row fade-in-up">
        <div class="chat-avatar user-avatar">
          <i class="bi bi-person-circle"></i>
        </div>
        <div class="chat-bubble user-bubble">
          <p class="bubble-text">${escapeHtml(text)}</p>
          <div class="bubble-footer">
            <span class="bubble-time">${time}</span>
            <span class="read-receipt" aria-label="Read receipt"><i class="bi bi-check2-all"></i></span>
          </div>
        </div>
      </div>
    `;
  };

  const buildAiBubble = (text, time, audioUrl) => {
    const speakBtn = audioUrl
      ? `<button class="btn btn-sm btn-link p-0 ms-1 speak-btn" data-audio="${escapeHtml(audioUrl)}" title="Play AI voice" aria-label="Play AI voice response"><i class="bi bi-volume-up-fill text-primary"></i></button>`
      : "";
    return `
    <div class="chat-row assistant-row fade-in-up">
      <div class="chat-avatar ai-avatar"><i class="bi bi-robot"></i></div>
      <div class="chat-bubble assistant-bubble">
        <p class="bubble-text">${escapeHtml(text)}</p>
        <div class="bubble-footer d-flex align-items-center gap-1">
          <span class="bubble-time">${time}</span>
          ${speakBtn}
        </div>
      </div>
    </div>`;
  };

  const showTypingIndicator = () => {
    const html = `
      <div id="typingIndicator" class="chat-row assistant-row fade-in-up">
        <div class="chat-avatar ai-avatar"><i class="bi bi-robot"></i></div>
        <div class="chat-bubble assistant-bubble" style="padding:12px 20px;">
          <p class="bubble-text mb-0 d-flex gap-1 align-items-center">
            <span class="spinner-grow spinner-grow-sm text-primary" role="status" style="animation-duration:.75s;width:8px;height:8px;"></span>
            <span class="spinner-grow spinner-grow-sm text-primary" role="status" style="animation-duration:.75s;animation-delay:.15s;width:8px;height:8px;"></span>
            <span class="spinner-grow spinner-grow-sm text-primary" role="status" style="animation-duration:.75s;animation-delay:.3s;width:8px;height:8px;"></span>
          </p>
        </div>
      </div>`;
    chatContainer.insertAdjacentHTML("beforeend", html);
    scrollToBottom();
  };

  const removeTypingIndicator = () => {
    const el = document.getElementById("typingIndicator");
    if (el) el.remove();
  };

  const escapeHtml = (text) => {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, (m) => map[m]);
  };

  // Update overall progress and breakdown metrics dynamically
  const updateDashboardStats = (scores) => {
    if (!scores) return;

    // Update overall progress ring
    const ring = document.querySelector(".progress-ring");
    if (ring) {
      ring.dataset.score = scores.overall;
      const ringVal = ring.querySelector(".progress-ring-value");
      if (ringVal) {
        ringVal.textContent = `${scores.overall}%`;
      }
      ring.style.setProperty("--score", String(scores.overall));
    }

    // Update breakdown metrics
    const metrics = [
      { label: "Fluency", score: scores.fluency },
      { label: "Grammar", score: scores.grammar },
      { label: "Vocabulary", score: scores.vocabulary },
      { label: "Pronunciation", score: scores.pronunciation },
      { label: "Confidence", score: scores.confidence }
    ];

    metrics.forEach((m) => {
      document.querySelectorAll(".metric-item").forEach((item) => {
        const labelText = item.querySelector(".metric-label")?.textContent.trim();
        if (labelText && labelText.includes(m.label)) {
          const bar = item.querySelector(".metric-bar");
          const scoreVal = item.querySelector("strong");
          if (bar) {
            bar.dataset.score = m.score;
            bar.style.width = `${m.score}%`;
          }
          if (scoreVal) {
            scoreVal.textContent = `${m.score}%`;
          }
        }
      });
    });
  };

  const updateCoachAnalysis = (data) => {
    const card = document.getElementById("coachAnalysisCard");
    const feedbackText = document.getElementById("analysisFeedback");
    const strengthsList = document.getElementById("analysisStrengths");
    const improvementsList = document.getElementById("analysisImprovements");
    const grammarSection = document.getElementById("grammarSection");
    const grammarList = document.getElementById("grammarSuggestionsList");

    if (!card) return;

    // Show card
    card.classList.remove("d-none");

    // Update feedback
    if (feedbackText) {
      feedbackText.textContent = data.feedback || "";
    }

    // Update strengths
    if (strengthsList) {
      strengthsList.innerHTML = "";
      if (data.strengths && data.strengths.length > 0) {
        data.strengths.forEach((str) => {
          const li = document.createElement("li");
          li.textContent = str;
          strengthsList.appendChild(li);
        });
      }
    }

    // Update improvements
    if (improvementsList) {
      improvementsList.innerHTML = "";
      if (data.improvements && data.improvements.length > 0) {
        data.improvements.forEach((imp) => {
          const li = document.createElement("li");
          li.textContent = imp;
          improvementsList.appendChild(li);
        });
      }
    }

    // Update grammar suggestions
    if (grammarSection && grammarList) {
      grammarList.innerHTML = "";
      if (data.grammar_suggestions && data.grammar_suggestions.length > 0) {
        grammarSection.classList.remove("d-none");
        data.grammar_suggestions.forEach((sug) => {
          const li = document.createElement("li");
          li.className = "suggestion-item small p-2 border rounded bg-danger-subtle d-flex align-items-center gap-2 mb-1";
          li.innerHTML = `
            <span class="text-decoration-line-through text-danger" style="font-size: 0.75rem;">${escapeHtml(sug.wrong)}</span>
            <i class="bi bi-arrow-right"></i>
            <span class="text-success fw-semibold" style="font-size: 0.75rem;">${escapeHtml(sug.right)}</span>
          `;
          grammarList.appendChild(li);
        });
      } else {
        grammarSection.classList.add("d-none");
      }
    }
  };


  // ── Simple toast notification ────────────────────────────────
  const showToast = (message) => {
    let container = document.getElementById("toastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "toastContainer";
      container.style.cssText = "position:fixed;bottom:80px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;";
      document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = "alert alert-info py-2 px-3 small shadow";
    toast.style.cssText = "max-width:300px;animation:fadeInUp .3s ease;";
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  };

  // ── AI TTS playback ─────────────────────────────────────────
  let currentAudio = null;

  const playAiAudio = (audioUrl) => {
    if (!audioUrl) return;
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    const audio = new Audio(audioUrl);
    currentAudio = audio;

    if (recordButton) recordButton.classList.add("ai-speaking");

    audio.addEventListener("ended", () => {
      if (recordButton) recordButton.classList.remove("ai-speaking");
      currentAudio = null;
    });
    audio.addEventListener("error", () => {
      if (recordButton) recordButton.classList.remove("ai-speaking");
      currentAudio = null;
      console.warn("AI audio playback error — check TTS output.");
    });

    audio.play().catch((e) => {
      if (recordButton) recordButton.classList.remove("ai-speaking");
      currentAudio = null;
      console.warn("Audio auto-play blocked by browser policy:", e.message);
      showToast("AI replied. Click the 🔊 button next to the message to hear it.");
    });
  };

  // ── Lock/unlock composer ────────────────────────────────────
  const lockComposer = () => {
    if (messageInput) { messageInput.disabled = true; }
    if (sendButton)   sendButton.disabled = true;
  };
  const unlockComposer = () => {
    if (messageInput) { messageInput.disabled = false; messageInput.focus(); }
    if (sendButton)   sendButton.disabled = false;
  };

  // ── Send text message ────────────────────────────────────────
  const sendMessage = async (text) => {
    if (!text || !text.trim()) return;
    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    chatContainer.insertAdjacentHTML("beforeend", buildUserBubble(text, timeStr));
    scrollToBottom();
    messageInput.value = "";
    lockComposer();
    showTypingIndicator();

    try {
      const formData = new FormData();
      formData.append("message", text);
      const response = await fetch("/dashboard/message", { method: "POST", body: formData });
      const data = await response.json();
      removeTypingIndicator();

      if (data.success) {
        chatContainer.insertAdjacentHTML("beforeend",
          buildAiBubble(data.ai_message.text, data.ai_message.time, data.ai_message.audio_url));
        scrollToBottom();
        playAiAudio(data.ai_message.audio_url);
        updateDashboardStats(data.scores);
        updateCoachAnalysis(data);
      } else {
        showToast(data.error || "An error occurred while communicating with the coach.");
      }
    } catch (err) {
      removeTypingIndicator();
      console.error(err);
      showToast("Network error: Could not reach the server.");
    } finally {
      unlockComposer();
    }
  };

  if (sendButton && messageInput) {
    sendButton.addEventListener("click", () => sendMessage(messageInput.value));
    messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(messageInput.value); }
    });
  }

  // ── Speak button (re-play TTS on demand) ────────────────────
  chatContainer.addEventListener("click", (e) => {
    const btn = e.target.closest(".speak-btn");
    if (btn) {
      const url = btn.dataset.audio;
      if (url) playAiAudio(url);
    }
  });

  // ── Audio recording ──────────────────────────────────────────
  let mediaRecorder = null;
  let audioChunks = [];
  let timerInterval = null;
  let elapsedSeconds = 0;
  let isRecording = false;

  const formatTime = (s) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  const startTimer = () => {
    elapsedSeconds = 0;
    if (voiceTimer) { voiceTimer.textContent = "00:00"; voiceTimer.classList.remove("d-none"); }
    timerInterval = setInterval(() => {
      elapsedSeconds++;
      if (voiceTimer) voiceTimer.textContent = formatTime(elapsedSeconds);
    }, 1000);
  };

  const stopTimer = () => {
    clearInterval(timerInterval);
    timerInterval = null;
    elapsedSeconds = 0;
    if (voiceTimer) { voiceTimer.classList.add("d-none"); voiceTimer.textContent = "00:00"; }
  };

  const setRecordingUI = (recording) => {
    isRecording = recording;
    if (!recordButton) return;
    if (recording) {
      recordButton.classList.add("recording");
      recordButton.setAttribute("aria-label", "Stop recording");
      recordButton.title = "Click to stop recording";
      if (messageInput) {
        messageInput.disabled = true;
        messageInput.placeholder = "🎙️ Recording… click mic again to send";
      }
    } else {
      recordButton.classList.remove("recording");
      recordButton.setAttribute("aria-label", "Voice input");
      recordButton.title = "Click to start recording";
      if (messageInput) {
        messageInput.disabled = false;
        messageInput.placeholder = "Type your message…";
      }
    }
  };

  const sendAudioMessage = async (audioBlob) => {
    lockComposer();
    showTypingIndicator();
    try {
      const formData = new FormData();
      const mimeType = audioBlob.type || "audio/webm";
      const ext = mimeType.includes("ogg") ? ".ogg" : mimeType.includes("mp4") ? ".mp4" : ".webm";
      formData.append("audio", audioBlob, `recording${ext}`);

      const response = await fetch("/dashboard/message", { method: "POST", body: formData });
      const data = await response.json();
      removeTypingIndicator();

      if (data.success) {
        chatContainer.insertAdjacentHTML("beforeend",
          buildUserBubble(data.user_message.text, data.user_message.time));
        chatContainer.insertAdjacentHTML("beforeend",
          buildAiBubble(data.ai_message.text, data.ai_message.time, data.ai_message.audio_url));
        scrollToBottom();
        playAiAudio(data.ai_message.audio_url);
        updateDashboardStats(data.scores);
        updateCoachAnalysis(data);
      } else {
        showToast(data.error || "An error occurred during audio processing.");
      }
    } catch (err) {
      removeTypingIndicator();
      console.error(err);
      showToast("Audio upload failed. Please check your connection.");
    } finally {
      unlockComposer();
    }
  };


  // ── Mic button click ─────────────────────────────────────────
  if (recordButton) {
    recordButton.addEventListener("click", async () => {
      if (currentAudio) { currentAudio.pause(); currentAudio = null; recordButton.classList.remove("ai-speaking"); }

      if (!isRecording) {
        audioChunks = [];
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });

          const preferredMime = [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/ogg;codecs=opus",
            "audio/mp4",
          ].find((m) => MediaRecorder.isTypeSupported(m)) || "";

          const recorderOptions = preferredMime ? { mimeType: preferredMime } : {};
          mediaRecorder = new MediaRecorder(stream, recorderOptions);

          mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) audioChunks.push(e.data);
          };

          mediaRecorder.onstop = async () => {
            stream.getTracks().forEach((t) => t.stop());
            if (audioChunks.length === 0) {
              showToast("No audio captured. Please try again.");
              return;
            }
            const audioBlob = new Blob(audioChunks, { type: preferredMime || "audio/webm" });
            await sendAudioMessage(audioBlob);
          };

          mediaRecorder.start(250);
          setRecordingUI(true);
          startTimer();
        } catch (err) {
          console.error("Microphone access error:", err);
          if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            showToast("⚠️ Microphone permission denied. Please allow access in your browser settings and reload.");
          } else if (err.name === "NotFoundError") {
            showToast("⚠️ No microphone found. Please connect a microphone and try again.");
          } else {
            showToast(`⚠️ Could not start recording: ${err.message}`);
          }
        }
      } else {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
          mediaRecorder.stop();
        }
        setRecordingUI(false);
        stopTimer();
      }
    });
  }

  // ── Keyboard shortcut: M key toggles mic (only when NOT in a text field) ──
  document.addEventListener("keydown", (e) => {
    const tag = document.activeElement?.tagName?.toLowerCase();
    const isEditable = document.activeElement?.isContentEditable;
    if (tag === "input" || tag === "textarea" || tag === "select" || isEditable) return;
    if (e.key.toLowerCase() === "m" && recordButton && !e.ctrlKey && !e.metaKey && !e.altKey) {
      recordButton.click();
    }
  });

  // ── Quick prompt buttons ─────────────────────────────────────
  document.querySelectorAll(".quick-prompt").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.querySelector("span")?.textContent;
      if (text) sendMessage(text.trim());
    });
  });

  // ── New Conversation button ──────────────────────────────────
  const newConvBtn = document.getElementById("newConversationButton");
  if (newConvBtn) {
    newConvBtn.addEventListener("click", async () => {
      try {
        const response = await fetch("/conversation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        if (response.ok) {
          const data = await response.json();
          window.location.href = `/conversation/${data.conversation_id}`;
        } else {
          showToast("Failed to create new conversation.");
        }
      } catch (err) {
        console.error(err);
        showToast("Network error: Could not start new conversation.");
      }
    });
  }

  // ── Date / time helpers ──────────────────────────────────────
  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    const now = new Date();
    const dDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const dNow  = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diff  = Math.floor((dNow - dDate) / 86400000);
    if (diff === 0) return "Today";
    if (diff === 1) return "Yesterday";
    if (diff < 7) return `${diff} Days Ago`;
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  const formatTimeOnly = (dateStr) =>
    new Date(dateStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  // ── Sidebar conversation list ────────────────────────────────
  const loadSidebarConversations = async () => {
    const listContainer = document.getElementById("sidebarConversationsList");
    if (!listContainer) return;
    try {
      const response = await fetch("/conversations");
      if (response.status === 401) { window.location.href = "/login"; return; }
      if (!response.ok) {
        listContainer.innerHTML = `<span class="text-danger small px-2" style="font-size:.7rem;">Error loading chats</span>`;
        return;
      }
      const conversations = await response.json();
      listContainer.innerHTML = "";
      if (conversations.length === 0) {
        listContainer.innerHTML = `
          <div class="text-muted text-center p-2 rounded bg-light" style="font-size:.7rem;line-height:1.2;">
            No conversations yet.<br>Click "New Conversation" to start.
          </div>`;
        return;
      }
      conversations.forEach((conv) => {
        const isCurrent = window.location.pathname === `/conversation/${conv.id}`;
        const activeClass = isCurrent ? "border-primary bg-primary-subtle" : "border-light bg-white";
        const badgeColor = conv.status === "in_progress" ? "bg-primary" : "bg-success";
        const badgeText  = conv.status === "in_progress" ? "In Progress" : "Completed";
        listContainer.insertAdjacentHTML("beforeend", `
          <a href="/conversation/${conv.id}" class="conversation-card p-2 border rounded text-decoration-none d-block ${activeClass} text-dark" style="font-size:.75rem;">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <strong class="text-truncate" style="max-width:110px;display:inline-block;">${escapeHtml(conv.topic)}</strong>
              <span class="badge ${badgeColor} text-white" style="font-size:.55rem;padding:2px 4px;">${badgeText}</span>
            </div>
            <div class="text-muted" style="font-size:.65rem;">${formatDate(conv.created_at)}</div>
          </a>`);
      });
    } catch (err) {
      console.error(err);
      const lc = document.getElementById("sidebarConversationsList");
      if (lc) lc.innerHTML = `<span class="text-danger small px-2" style="font-size:.7rem;">Network error</span>`;
    }
  };
  loadSidebarConversations();

  // ── Load conversation messages into chat area ────────────────
  const loadConversation = async (conversationId) => {
    const cc = document.getElementById("chatMessages");
    if (!cc) return;
    cc.innerHTML = "";
    showTypingIndicator();
    try {
      const response = await fetch(`/conversation/${conversationId}`, { headers: { Accept: "application/json" } });
      removeTypingIndicator();
      if (response.status === 401) { window.location.href = "/login"; return; }
      if (response.status === 403) { showToast("Access Denied: You do not own this conversation."); return; }
      if (!response.ok) { showToast("Failed to load conversation messages."); return; }
      const data = await response.json();
      const headerTitle = document.querySelector(".panel-title");
      if (headerTitle) headerTitle.textContent = data.conversation.topic || "Conversation";
      cc.innerHTML = "";
      const messages = data.messages;
      if (messages.length === 0) {
        cc.innerHTML = `<div class="text-muted text-center p-4" style="font-size:.9rem;">No messages yet.<br>Start your conversation below.</div>`;
        return;
      }
      messages.forEach((msg) => {
        const role = msg.sender.toLowerCase() === "ai" ? "assistant" : "user";
        cc.insertAdjacentHTML("beforeend",
          role === "assistant"
            ? buildAiBubble(msg.message, formatTimeOnly(msg.created_at), null)
            : buildUserBubble(msg.message, formatTimeOnly(msg.created_at)));
      });
      scrollToBottom();
    } catch (err) {
      removeTypingIndicator();
      console.error(err);
      showToast("Network error: Failed to retrieve messages.");
    }
  };

  // ── Sidebar conversation card clicks (SPA navigation) ────────
  const listContainer = document.getElementById("sidebarConversationsList");
  if (listContainer) {
    listContainer.addEventListener("click", async (e) => {
      const card = e.target.closest(".conversation-card");
      if (!card) return;
      e.preventDefault();
      const href  = card.getAttribute("href");
      const convId = href.split("/").pop();
      history.pushState({ conversationId: convId }, "", href);
      document.querySelectorAll(".conversation-card").forEach((c) => {
        c.classList.remove("border-primary", "bg-primary-subtle");
        c.classList.add("border-light", "bg-white");
      });
      card.classList.remove("border-light", "bg-white");
      card.classList.add("border-primary", "bg-primary-subtle");
      await loadConversation(convId);
    });
  }

  window.addEventListener("popstate", async () => {
    const parts = window.location.pathname.split("/");
    if (parts.includes("conversation")) {
      const convId = parts.pop();
      document.querySelectorAll(".conversation-card").forEach((c) => {
        const cId = c.getAttribute("href").split("/").pop();
        if (cId === convId) { c.classList.add("border-primary","bg-primary-subtle"); c.classList.remove("border-light","bg-white"); }
        else { c.classList.remove("border-primary","bg-primary-subtle"); c.classList.add("border-light","bg-white"); }
      });
      await loadConversation(convId);
    } else if (window.location.pathname === "/dashboard") {
      window.location.reload();
    }
  });

  // ── End Session button ───────────────────────────────────────
  const endSessionBtn = document.getElementById("endSessionButton");
  if (endSessionBtn) {
    endSessionBtn.addEventListener("click", async () => {
      const card = document.querySelector(".conversation-card.border-primary");
      let convId = card ? card.getAttribute("href").split("/").pop() : null;
      if (!convId) {
        const parts = window.location.pathname.split("/");
        if (parts.includes("conversation")) convId = parts.pop();
      }
      if (!convId) {
        try {
          const res = await fetch("/conversations");
          if (res.ok) {
            const list = await res.json();
            if (list.length > 0 && list[0].status === "in_progress") convId = list[0].id;
          }
        } catch (e) { console.error(e); }
      }
      if (!convId) { showToast("No active conversation session to end."); return; }

      const origText = endSessionBtn.innerHTML;
      endSessionBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Ending…`;
      endSessionBtn.disabled = true;

      try {
        const response = await fetch(`/conversation/${convId}/complete`, { method: "POST" });
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            document.getElementById("reportTopic").textContent      = data.report.topic || "Practice Session";
            document.getElementById("reportMeta").textContent       = `Duration: ${data.report.duration_minutes} Mins | ${data.report.total_messages} Messages`;
            document.getElementById("reportOverallScore").textContent = `${data.report.overall_score}%`;
            const metricsContainer = document.getElementById("reportMetricsContainer");
            if (metricsContainer) {
              metricsContainer.innerHTML = "";
              const tones = { grammar:"success", vocabulary:"warning", fluency:"primary", confidence:"danger", pronunciation:"info" };
              for (const [key, val] of Object.entries(data.report.metrics)) {
                const tone = tones[key] || "primary";
                const label = key.charAt(0).toUpperCase() + key.slice(1);
                metricsContainer.insertAdjacentHTML("beforeend", `
                  <div class="col-6"><div class="p-2 border rounded bg-light">
                    <div class="d-flex justify-content-between align-items-center mb-1" style="font-size:.7rem;">
                      <span class="fw-semibold">${label}</span><strong>${val}%</strong>
                    </div>
                    <div class="progress" style="height:4px;">
                      <div class="progress-bar bg-${tone}" role="progressbar" style="width:${val}%;" aria-valuenow="${val}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                  </div></div>`);
              }
            }
            const mistakesList = document.getElementById("reportMistakesList");
            if (mistakesList) {
              mistakesList.innerHTML = "";
              data.report.mistakes.forEach((m) => {
                const li = document.createElement("li"); li.className = "mb-1"; li.textContent = m;
                mistakesList.appendChild(li);
              });
            }
            document.getElementById("reportHomeworkText").textContent = data.report.homework || "";
            new bootstrap.Modal(document.getElementById("sessionReportModal")).show();
            await loadSidebarConversations();
          }
        } else {
          showToast("Failed to complete conversation session.");
        }
      } catch (err) {
        console.error(err);
        showToast("Network error: Could not complete session.");
      } finally {
        endSessionBtn.innerHTML = origText;
        endSessionBtn.disabled = false;
      }
    });
  }

  // ── Sidebar link helpers ─────────────────────────────────────
  const scrollToEl = (selector) => {
    const el = document.querySelector(selector);
    if (el) { el.scrollIntoView({ behavior: "smooth" }); el.style.outline = "2px solid var(--dashboard-primary, #6366f1)"; setTimeout(() => (el.style.outline = ""), 1500); }
  };

  document.getElementById("sidebarConversationsLink")?.addEventListener("click", (e) => { e.preventDefault(); document.getElementById("sidebarConversationsList")?.scrollIntoView({ behavior: "smooth" }); });
  document.getElementById("sidebarPracticeLink")?.addEventListener("click", (e) => { e.preventDefault(); document.getElementById("newConversationButton")?.click(); });
  document.getElementById("sidebarProgressLink")?.addEventListener("click", (e) => { e.preventDefault(); scrollToEl(".progress-panel, .surface-panel"); });
  document.getElementById("sidebarGoalLink")?.addEventListener("click", (e) => { e.preventDefault(); scrollToEl(".sidebar-widget"); });
  document.getElementById("sidebarFeedbackLink")?.addEventListener("click", (e) => { e.preventDefault(); scrollToEl("#coachAnalysisCard, .recent-panel"); });

  // ── Settings modal ───────────────────────────────────────────
  document.getElementById("sidebarSettingsLink")?.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("/dashboard/settings");
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          document.getElementById("settingsNativeLang").value = data.native_language || "English";
          document.getElementById("settingsGroqKey").value = data.groq_api_key || "";
          new bootstrap.Modal(document.getElementById("settingsModal")).show();
        }
      }
    } catch (err) { console.error(err); }
  });

  document.getElementById("settingsForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      const response = await fetch("/dashboard/settings", { method: "POST", body: formData });
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const modalEl = document.getElementById("settingsModal");
          bootstrap.Modal.getInstance(modalEl)?.hide();
          showToast("✅ Settings saved! Please continue practicing.");
          setTimeout(() => window.location.reload(), 1500);
        }
      }
    } catch (err) { console.error(err); showToast("Failed to save settings."); }
  });

}); // end DOMContentLoaded
