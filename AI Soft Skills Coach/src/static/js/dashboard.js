/* ========================
   Sidebar Toggle
======================== */
const sidebarToggle = document.getElementById("sidebarToggle");
const dashboardSidebar = document.getElementById("dashboardSidebar");

if (sidebarToggle && dashboardSidebar) {
  sidebarToggle.addEventListener("click", () => {
    const isOpen = dashboardSidebar.classList.toggle("open");
    sidebarToggle.setAttribute("aria-expanded", String(isOpen));
  });

  document.addEventListener("click", (event) => {
    if (window.innerWidth >= 1200) {
      return;
    }

    const clickedInsideSidebar = dashboardSidebar.contains(event.target);
    const clickedToggle = sidebarToggle.contains(event.target);

    if (!clickedInsideSidebar && !clickedToggle) {
      dashboardSidebar.classList.remove("open");
      sidebarToggle.setAttribute("aria-expanded", "false");
    }
  });
}

/* ========================
   Theme Toggle
======================== */
const themeToggle = document.getElementById("themeToggle");

const applyTheme = (theme) => {
  document.documentElement.setAttribute("data-theme", theme);
  if (themeToggle) {
    themeToggle.setAttribute("aria-pressed", String(theme === "dark"));
    themeToggle.innerHTML =
      theme === "dark"
        ? '<i class="bi bi-sun"></i>'
        : '<i class="bi bi-moon-stars"></i>';
  }
};

const savedTheme = localStorage.getItem("speakai-theme");
if (savedTheme === "dark" || savedTheme === "light") {
  applyTheme(savedTheme);
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const current =
      document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    localStorage.setItem("speakai-theme", next);
    applyTheme(next);
  });
}

/* ========================
   Ripple Effect
======================== */
const rippleButtons = document.querySelectorAll(".ripple-btn");

rippleButtons.forEach((button) => {
  button.addEventListener("click", (event) => {
    const ripple = document.createElement("span");
    ripple.className = "ripple";

    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = `${size}px`;
    ripple.style.height = `${size}px`;
    ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${event.clientY - rect.top - size / 2}px`;

    const oldRipple = button.querySelector(".ripple");
    if (oldRipple) {
      oldRipple.remove();
    }

    button.appendChild(ripple);
  });
});

/* ========================
   Dashboard Score Visuals
======================== */
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
});
