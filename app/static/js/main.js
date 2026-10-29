/**
 * SkillSwap Client Core Script
 * Integrates real-time Socket.IO alerts and interactive SymPy point previewing.
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Initialize Real-Time WebSockets (Socket.IO)
  initSocketIO();

  // 2. Initialize Live SymPy Point Calculator if on create/edit offer page
  initPointCalculator();
});

function initSocketIO() {
  if (typeof io === "undefined") {
    return;
  }

  const socket = io({
    transports: ["websocket", "polling"],
  });

  socket.on("connect", () => {
    console.log("[SkillSwap Socket] Connected to real-time notification gateway.");
  });

  socket.on("new_notification", (notif) => {
    console.log("[SkillSwap Socket] Notification received:", notif);
    
    // Display interactive Toast alert
    showToast(notif.title, notif.message, notif.link);

    // Increment notification badge counter
    const badge = document.getElementById("nav-unread-badge");
    if (badge) {
      let count = parseInt(badge.innerText, 10) || 0;
      count += 1;
      badge.innerText = count;
      badge.style.display = "inline-flex";
    }
  });

  socket.on("disconnect", () => {
    console.log("[SkillSwap Socket] Disconnected from server.");
  });
}

function showToast(title, message, link) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = "toast-message";
  toast.innerHTML = `
    <div style="flex: 1;">
      <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 2px;">${escapeHtml(title)}</div>
      <div style="font-size: 0.85rem; color: #cbd5e1;">${escapeHtml(message)}</div>
    </div>
    ${link ? `<a href="${link}" style="color: #818cf8; font-weight: 600; font-size: 0.85rem; text-decoration: underline;">View</a>` : ""}
  `;

  container.appendChild(toast);

  // Auto remove after 6 seconds
  setTimeout(() => {
    toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 400);
  }, 6000);
}

function initPointCalculator() {
  const durationInput = document.getElementById("duration_minutes");
  const levelSelect = document.getElementById("proficiency_level");
  const prepSelect = document.getElementById("preparation_effort");

  if (!durationInput || !levelSelect) {
    return;
  }

  const updatePreview = () => {
    const duration = parseInt(durationInput.value, 10) || 60;
    const level = levelSelect.value || "intermediate";
    const prep = prepSelect ? parseInt(prepSelect.value, 10) || 1 : 1;

    // Fetch exact calculation from backend SymPy API
    fetch(`/matching/api/preview-points?duration=${duration}&level=${level}&prep=${prep}`)
      .then((res) => res.json())
      .then((data) => {
        const pointsBadge = document.getElementById("preview-points-val");
        const diffBadge = document.getElementById("preview-difficulty-val");
        const formulaBreakdown = document.getElementById("preview-formula-breakdown");

        if (pointsBadge) pointsBadge.innerText = `${data.points} pts`;
        if (diffBadge) {
          diffBadge.innerText = data.difficulty;
          diffBadge.className = `badge badge-level-${data.difficulty.toLowerCase()}`;
        }
        if (formulaBreakdown && data.breakdown) {
          formulaBreakdown.innerHTML = `
            <div><strong>Formula:</strong> (${data.breakdown.duration_minutes}m / 30) × 10 × ${data.breakdown.multiplier} + Prep Bonus (${data.breakdown.preparation_bonus} pts)</div>
            <div style="margin-top: 4px; font-size: 0.85rem; color: #64748b;">SymPy symbolic proof: ${data.breakdown.symbolic_formula}</div>
          `;
        }
      })
      .catch((err) => console.error("Error evaluating points:", err));
  };

  durationInput.addEventListener("input", updatePreview);
  levelSelect.addEventListener("change", updatePreview);
  if (prepSelect) prepSelect.addEventListener("change", updatePreview);

  // Initial trigger
  updatePreview();
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, (m) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[m]));
}
