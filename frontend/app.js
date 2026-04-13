/* ============================================
   Job Engine — Frontend Logic
   ============================================ */

const API = "https://tanishapritha-job-crew.hf.space";

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

// ---- Search Jobs Now ----
$("#btn-search-now").addEventListener("click", async () => {
  const btn = $("#btn-search-now");
  const msg = $("#search-status-msg");
  const domains = $("#pref-domains").value.trim();

  if (!domains) {
    flashMsg(msg, "Enter job titles first", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Searching...";
  flashMsg(msg, "", "");

  try {
    const jobs = await api("searchJobs", {
      domains: domains,
      location_1: $("#pref-loc1").value.trim(),
      location_2: $("#pref-loc2").value.trim(),
      location_3: $("#pref-loc3").value.trim(),
    });

    renderJobs(jobs);

    // Switch to Jobs tab
    $$(".dash-tab").forEach(t => t.classList.remove("active"));
    $$(".section").forEach(s => s.classList.remove("active"));
    document.querySelector('[data-section="jobs"]').classList.add("active");
    $("#section-jobs").classList.add("active");

    flashMsg(msg, `Found ${jobs.length} jobs`, "success");
  } catch (err) {
    flashMsg(msg, err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Search Jobs Now";
  }
});

function renderJobs(jobs) {
  const grid = $("#jobs-grid");
  const empty = $("#jobs-empty");
  const count = $("#jobs-count");

  if (!jobs || jobs.length === 0) {
    grid.innerHTML = "";
    empty.style.display = "block";
    count.textContent = "";
    return;
  }

  empty.style.display = "none";
  count.textContent = `${jobs.length} jobs found`;

  grid.innerHTML = jobs.map(job => {
    const source = (job.source || "unknown").toLowerCase();
    const sourceLabel = source.charAt(0).toUpperCase() + source.slice(1);
    const sourceClass = `job-source job-source-${source}`;
    const location = job.location || "Location not specified";
    const company = job.company || "Unknown Company";
    const url = job.redirect_url || "#";
    const domain = job.matched_domain || "";

    return `
      <div class="job-card">
        <div class="job-info">
          <div class="job-title">${escapeHtml(job.title)}</div>
          <div class="job-company">${escapeHtml(company)}</div>
          <div class="job-meta">
            <span class="job-location">${escapeHtml(location)}</span>
            <span class="${sourceClass}">${sourceLabel}</span>
            ${domain ? `<span class="job-domain">${escapeHtml(domain)}</span>` : ""}
          </div>
        </div>
        <div class="job-actions">
          <a href="${escapeHtml(url)}" target="_blank" rel="noopener" class="btn-apply">Apply</a>
        </div>
      </div>
    `;
  }).join("");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

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
