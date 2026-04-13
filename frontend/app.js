/* ============================================
   Job Engine — Frontend Logic
   ============================================ */

const API = "http://127.0.0.1:8000";

// ---- State ----
let currentUser = null;

// ---- Helpers ----
async function api(action, payload = {}) {
  const res = await fetch(`${API}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, payload }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data.data;
}

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function showScreen(id) {
  $$(".screen").forEach(s => s.classList.remove("active"));
  $(`#${id}`).classList.add("active");
}

function flashMsg(el, text, type = "success") {
  el.textContent = text;
  el.className = `inline-msg ${type}`;
  setTimeout(() => { el.textContent = ""; }, 3000);
}

// ---- Auth tabs ----
$$(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    $$(".tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    $$(".auth-form").forEach(f => f.classList.remove("active"));
    $(`#${tab.dataset.tab}-form`).classList.add("active");
    $("#auth-error").textContent = "";
  });
});

// ---- Register ----
$("#register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  btn.disabled = true;
  btn.textContent = "Creating...";
  $("#auth-error").textContent = "";

  try {
    await api("register", {
      name: $("#reg-name").value.trim(),
      email: $("#reg-email").value.trim(),
      password: $("#reg-password").value,
    });

    // Auto-login after register
    const profile = await api("login", {
      email: $("#reg-email").value.trim(),
      password: $("#reg-password").value,
    });
    loginSuccess(profile);
  } catch (err) {
    $("#auth-error").textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Create Account";
  }
});

// ---- Login ----
$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  btn.disabled = true;
  btn.textContent = "Signing in...";
  $("#auth-error").textContent = "";

  try {
    const profile = await api("login", {
      email: $("#login-email").value.trim(),
      password: $("#login-password").value,
    });
    loginSuccess(profile);
  } catch (err) {
    $("#auth-error").textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Sign In";
  }
});

// ---- Post-login ----
function loginSuccess(profile) {
  currentUser = profile;
  localStorage.setItem("user", JSON.stringify(profile));
  renderDashboard();
  showScreen("dashboard-screen");
}

function renderDashboard() {
  if (!currentUser) return;

  const firstName = (currentUser.name || "User").split(" ")[0];
  $("#user-greeting").textContent = `Hi, ${firstName}`;

  // Profile
  $("#prof-name").textContent = currentUser.name || "—";
  $("#prof-email").textContent = currentUser.email || "—";
  $("#prof-uid").textContent = currentUser.user_id || "—";
  $("#prof-emails-sent").textContent = currentUser.emails_sent || "0";
  $("#prof-daily-limit").textContent = currentUser.daily_limit || "25";

  // Status badge
  const status = (currentUser.status || "active").toLowerCase();
  const statusEl = $("#prof-status");
  statusEl.textContent = status;
  statusEl.className = `info-value badge badge-${status}`;
  $("#status-current").textContent = status;

  // Preferences
  $("#pref-domains").value = currentUser.domains || "";
  $("#pref-loc1").value = currentUser.location_1 || "";
  $("#pref-loc2").value = currentUser.location_2 || "";
  $("#pref-loc3").value = currentUser.location_3 || "";
  $("#pref-remote").checked = (currentUser.remote_jobs || "").toLowerCase() === "true";
  $("#pref-experience").value = currentUser.experience_level || "beginner";
  $("#pref-salary").value = currentUser.min_salary || "";
}

// ---- Dashboard tabs ----
$$(".dash-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    $$(".dash-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    $$(".section").forEach(s => s.classList.remove("active"));
    $(`#section-${tab.dataset.section}`).classList.add("active");
  });
});

// ---- Save preferences ----
$("#pref-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  const msg = $("#pref-status-msg");
  btn.disabled = true;
  btn.textContent = "Saving...";

  try {
    // Update domains
    await api("updateDomains", {
      user_id: currentUser.user_id,
      domains: $("#pref-domains").value.trim(),
    });

    // Update profile fields
    await api("updateUserProfile", {
      user_id: currentUser.user_id,
      location_1: $("#pref-loc1").value.trim(),
      location_2: $("#pref-loc2").value.trim(),
      location_3: $("#pref-loc3").value.trim(),
      remote_jobs: $("#pref-remote").checked ? "true" : "false",
      experience_level: $("#pref-experience").value,
      min_salary: $("#pref-salary").value || "0",
    });

    // Refresh profile
    const profile = await api("login", {
      email: currentUser.email,
      password: localStorage.getItem("_pw"),
    });
    currentUser = profile;
    localStorage.setItem("user", JSON.stringify(profile));
    renderDashboard();
    flashMsg(msg, "Saved", "success");
  } catch (err) {
    flashMsg(msg, err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Save Preferences";
  }
});

// ---- Status actions ----
async function setStatus(newStatus) {
  const msg = $("#status-msg");
  try {
    const action = newStatus === "unsubscribed" ? "unsubscribeUser" : "toggleUserStatus";
    const payload = newStatus === "unsubscribed"
      ? { user_id: currentUser.user_id }
      : { user_id: currentUser.user_id, status: newStatus };
    await api(action, payload);

    currentUser.status = newStatus;
    localStorage.setItem("user", JSON.stringify(currentUser));
    renderDashboard();
    flashMsg(msg, `Status changed to ${newStatus}`, "success");
  } catch (err) {
    flashMsg(msg, err.message, "error");
  }
}

$("#btn-pause").addEventListener("click", () => setStatus("paused"));
$("#btn-activate").addEventListener("click", () => setStatus("active"));
$("#btn-unsubscribe").addEventListener("click", () => {
  if (confirm("Are you sure you want to unsubscribe? You will stop receiving job alerts.")) {
    setStatus("unsubscribed");
  }
});

// ---- Logout ----
$("#logout-btn").addEventListener("click", () => {
  currentUser = null;
  localStorage.removeItem("user");
  localStorage.removeItem("_pw");
  showScreen("auth-screen");
  // Reset forms
  $("#login-form").reset();
  $("#register-form").reset();
  $("#auth-error").textContent = "";
});

// ---- Store password for profile refresh (client-side only) ----
// This is stored temporarily so we can re-fetch the profile after updates.
// In production, use a JWT token instead.
const origLoginSubmit = $("#login-form").onsubmit;
$("#login-form").addEventListener("submit", () => {
  localStorage.setItem("_pw", $("#login-password").value);
});
$("#register-form").addEventListener("submit", () => {
  localStorage.setItem("_pw", $("#reg-password").value);
});

// ---- Auto-login from localStorage ----
(function init() {
  const saved = localStorage.getItem("user");
  if (saved) {
    try {
      currentUser = JSON.parse(saved);
      renderDashboard();
      showScreen("dashboard-screen");
    } catch {
      localStorage.removeItem("user");
    }
  }
})();
