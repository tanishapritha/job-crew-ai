import React, { useState, useEffect } from "react";
import { 
  Briefcase, 
  User, 
  Settings, 
  Activity, 
  Search, 
  LogOut, 
  Moon, 
  Sun, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  ExternalLink,
  MapPin,
  Building2,
  DollarSign
} from "lucide-react";

const API_URL = "https://tanishapritha-job-crew.hf.space";

// --- Components ---

const ThemeToggle = ({ theme, toggleTheme }) => (
  <button onClick={toggleTheme} className="btn btn-ghost" title="Toggle theme">
    {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
  </button>
);

const Badge = ({ variant, children }) => {
  const className = `badge badge-${variant || "other"}`;
  return <span className={className}>{children}</span>;
};

// --- App ---

export default function App() {
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("user")) || null);
  const [screen, setScreen] = useState("profile"); // profile, preferences, jobs, status
  const [isAuth, setIsAuth] = useState(!!user);
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === "light" ? "dark" : "light");

  const apiFetch = async (action, payload = {}) => {
    setError("");
    try {
      const res = await fetch(`${API_URL}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, payload }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");
      return data.data;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("_pw");
    setUser(null);
    setIsAuth(false);
  };

  if (!isAuth) {
    return (
      <AuthScreen 
        onLogin={(u) => { setUser(u); setIsAuth(true); }} 
        apiFetch={apiFetch} 
        theme={theme} 
        toggleTheme={toggleTheme}
      />
    );
  }

  return (
    <div className="app-container">
      <Sidebar 
        current={screen} 
        setScreen={setScreen} 
        onLogout={handleLogout} 
        user={user}
        theme={theme}
        toggleTheme={toggleTheme}
      />
      <main className="main-content animate-in">
        <Header user={user} screen={screen} />
        {screen === "profile" && <ProfileSection user={user} />}
        {screen === "preferences" && <PreferencesSection user={user} apiFetch={apiFetch} setUser={setUser} setJobs={setJobs} setScreen={setScreen} />}
        {screen === "jobs" && <JobsSection jobs={jobs} />}
        {screen === "status" && <StatusSection user={user} apiFetch={apiFetch} setUser={setUser} />}
        {error && <div className="error-banner card animate-in"><AlertCircle size={16} /> {error}</div>}
      </main>
    </div>
  );
}

// --- Auth Section ---

const AuthScreen = ({ onLogin, apiFetch, theme, toggleTheme }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLocalError("");
    try {
      if (isRegister) {
        await apiFetch("register", formData);
      }
      const profile = await apiFetch("login", { email: formData.email, password: formData.password });
      localStorage.setItem("user", JSON.stringify(profile));
      localStorage.setItem("_pw", formData.password);
      onLogin(profile);
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="card" style={{ width: "100%", maxWidth: "400px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
          <div>
            <h1 style={{ fontSize: "1.5rem" }}>Job Engine</h1>
            <p className="subtitle" style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>{isRegister ? "Join the automation" : "Welcome back"}</p>
          </div>
          <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {isRegister && (
            <div className="input-group">
              <label>Full Name</label>
              <input 
                type="text" 
                placeholder="Jane Doe" 
                value={formData.name}
                onChange={e => setFormData({...formData, name: e.target.value})}
                required 
              />
            </div>
          )}
          <div className="input-group">
            <label>Email</label>
            <input 
              type="email" 
              placeholder="jane@example.com" 
              value={formData.email}
              onChange={e => setFormData({...formData, email: e.target.value})}
              required 
            />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input 
              type="password" 
              placeholder="••••••••" 
              value={formData.password}
              onChange={e => setFormData({...formData, password: e.target.value})}
              required 
            />
          </div>
          {localError && <p className="error-msg" style={{ color: "var(--danger)", fontSize: "0.875rem" }}><AlertCircle size={14} style={{ verticalAlign: "middle", marginRight: "4px" }}/> {localError}</p>}
          <button type="submit" className="btn btn-primary" style={{ marginTop: "0.5rem" }} disabled={loading}>
            {loading ? "Processing..." : (isRegister ? "Create Account" : "Sign In")}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.875rem", color: "var(--text-muted)" }}>
          {isRegister ? "Already have an account?" : "Don't have an account?"} {" "}
          <button 
            type="button" 
            className="btn-link" 
            style={{ background: "none", border: "none", color: "var(--primary)", padding: 0 }}
            onClick={() => setIsRegister(!isRegister)}
          >
            {isRegister ? "Sign In" : "Register"}
          </button>
        </p>
      </div>
    </div>
  );
};

// --- Dashboard Sections ---

const Sidebar = ({ current, setScreen, onLogout, user, theme, toggleTheme }) => {
  const navItems = [
    { id: "profile", label: "Profile", icon: User },
    { id: "preferences", label: "Preferences", icon: Settings },
    { id: "jobs", label: "Jobs", icon: Briefcase },
    { id: "status", label: "System Status", icon: Activity },
  ];

  return (
    <aside className="sidebar card" style={{ height: "100vh", position: "sticky", top: 0, borderRadius: 0, borderTop: "none", borderBottom: "none", width: "260px", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "1.5rem", borderBottom: "1px solid var(--border)" }}>
        <h2 style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "1.25rem" }}>
          <Briefcase size={22} color="var(--primary)" />
          JobEngine
        </h2>
      </div>
      
      <nav style={{ padding: "1rem", flex: 1 }}>
        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {navItems.map(item => (
            <li key={item.id}>
              <button 
                onClick={() => setScreen(item.id)}
                className={`btn btn-ghost`}
                style={{ 
                  width: "100%", 
                  justifyContent: "flex-start",
                  background: current === item.id ? "var(--surface-hover)" : "transparent",
                  color: current === item.id ? "var(--text)" : "var(--text-muted)",
                  fontWeight: current === item.id ? "600" : "400"
                }}
              >
                <item.icon size={18} />
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div style={{ padding: "1rem", borderTop: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
          <button onClick={onLogout} className="btn btn-ghost" style={{ color: "var(--danger)" }}>
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </aside>
  );
};

const Header = ({ user, screen }) => {
  const titles = {
    profile: "Account Profile",
    preferences: "Automation Settings",
    jobs: "Job Discoveries",
    status: "Service Monitoring"
  };

  return (
    <header style={{ marginBottom: "2.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div>
        <h1 style={{ fontSize: "1.875rem", marginBottom: "0.25rem" }}>{titles[screen]}</h1>
        <p style={{ color: "var(--text-muted)" }}>Control and monitor your automated job hunt.</p>
      </div>
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", padding: "0.5rem 1rem", borderRadius: "var(--radius-lg)", display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <div style={{ width: "32px", height: "32px", background: "var(--primary)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: "0.875rem", fontWeight: "600" }}>
          {user.name[0]}
        </div>
        <div>
          <p style={{ fontSize: "0.75rem", fontWeight: "500" }}>{user.name}</p>
          <p style={{ fontSize: "0.625rem", color: "var(--text-muted)" }}>{user.status}</p>
        </div>
      </div>
    </header>
  );
};

const ProfileSection = ({ user }) => (
  <div className="animate-in" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.5rem" }}>
    <div className="card">
      <h3 style={{ marginBottom: "1.5rem", fontSize: "1.125rem" }}>Identity</h3>
      <div className="info-list" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <InfoItem label="Full Name" value={user.name} />
        <InfoItem label="Email Address" value={user.email} />
        <InfoItem label="User ID" value={user.user_id} monospace />
      </div>
    </div>
    <div className="card">
      <h3 style={{ marginBottom: "1.5rem", fontSize: "1.125rem" }}>Engagement</h3>
      <div className="stats-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <StatCard label="Emails Sent" value={user.emails_sent || 0} icon={CheckCircle2} color="var(--success)" />
        <StatCard label="Daily Limit" value={user.daily_limit || 25} icon={Clock} color="var(--primary)" />
      </div>
    </div>
  </div>
);

const PreferencesSection = ({ user, apiFetch, setUser, setJobs, setScreen }) => {
  const [prefs, setPrefs] = useState({
    domains: user.domains || "",
    location_1: user.location_1 || "",
    location_2: user.location_2 || "",
    location_3: user.location_3 || "",
    remote_jobs: user.remote_jobs?.toLowerCase() === "true",
    experience_level: user.experience_level || "beginner",
    min_salary: user.min_salary || ""
  });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    try {
      await apiFetch("updateDomains", { user_id: user.user_id, domains: prefs.domains });
      await apiFetch("updateUserProfile", { ...prefs, user_id: user.user_id, remote_jobs: prefs.remote_jobs ? "true" : "false" });
      const password = localStorage.getItem("_pw");
      const updated = await apiFetch("login", { email: user.email, password });
      setUser(updated);
      localStorage.setItem("user", JSON.stringify(updated));
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleSearchNow = async () => {
    setSaving(true);
    try {
      const results = await apiFetch("searchJobs", { 
        domains: prefs.domains, 
        location_1: prefs.location_1, 
        location_2: prefs.location_2, 
        location_3: prefs.location_3 
      });
      setJobs(results);
      setScreen("jobs");
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="animate-in card">
      <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
        <div className="input-group">
          <label style={{ display: "flex", justifyContent: "space-between" }}>
            Target Job Titles
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Semicolon separated</span>
          </label>
          <input 
            type="text" 
            placeholder="Python Developer; Data Analyst" 
            value={prefs.domains} 
            onChange={e => setPrefs({...prefs, domains: e.target.value})}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
          <div className="input-group">
            <label>Location 1</label>
            <input type="text" value={prefs.location_1} onChange={e => setPrefs({...prefs, location_1: e.target.value})} />
          </div>
          <div className="input-group">
            <label>Location 2</label>
            <input type="text" value={prefs.location_2} onChange={e => setPrefs({...prefs, location_2: e.target.value})} />
          </div>
          <div className="input-group">
            <label>Location 3</label>
            <input type="text" value={prefs.location_3} onChange={e => setPrefs({...prefs, location_3: e.target.value})} />
          </div>
        </div>

        <div style={{ display: "flex", gap: "2rem", alignItems: "flex-end" }}>
          <div className="input-group" style={{ flex: 1 }}>
            <label>Experience Level</label>
            <select value={prefs.experience_level} onChange={e => setPrefs({...prefs, experience_level: e.target.value})}>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="senior">Senior</option>
            </select>
          </div>
          <div className="input-group" style={{ flex: 1 }}>
            <label>Minimum Salary (INR)</label>
            <input type="number" value={prefs.min_salary} onChange={e => setPrefs({...prefs, min_salary: e.target.value})} />
          </div>
          <div style={{ paddingBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input 
              type="checkbox" 
              id="remote" 
              checked={prefs.remote_jobs} 
              onChange={e => setPrefs({...prefs, remote_jobs: e.target.checked})} 
              style={{ width: "16px", height: "16px" }}
            />
            <label htmlFor="remote" style={{ cursor: "pointer" }}>Inlcude Remote</label>
          </div>
        </div>

        <div style={{ borderTop: "1px solid var(--border)", paddingTop: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", gap: "1rem" }}>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving..." : "Save Preferences"}
            </button>
            <button type="button" onClick={handleSearchNow} className="btn" style={{ background: "rgba(37, 99, 235, 0.1)", color: "var(--primary)", border: "1px solid transparent" }} disabled={saving}>
              <Search size={16} /> 
              Search Now
            </button>
          </div>
          {success && <p style={{ color: "var(--success)", fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "0.25rem" }}><CheckCircle2 size={16}/> Settings updated</p>}
        </div>
      </form>
    </div>
  );
};

const JobsSection = ({ jobs }) => (
  <div className="animate-in">
    {!jobs || jobs.length === 0 ? (
      <div className="card" style={{ textAlign: "center", padding: "4rem" }}>
        <Briefcase size={48} style={{ color: "var(--text-muted)", marginBottom: "1rem", opacity: 0.5 }} />
        <p style={{ color: "var(--text-muted)" }}>No live discoveries yet. Run a search from Preferences.</p>
      </div>
    ) : (
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {jobs.map((job, idx) => (
          <div key={idx} className="card job-card-wide" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
                <h4 style={{ fontSize: "1.0625rem" }}>{job.title}</h4>
                <Badge variant={job.source?.toLowerCase()}>{job.source}</Badge>
              </div>
              <div style={{ display: "flex", gap: "1.5rem", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}><Building2 size={14}/> {job.company}</span>
                <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}><MapPin size={14}/> {job.location}</span>
                {job.salary && <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}><DollarSign size={14}/> {job.salary}</span>}
              </div>
            </div>
            <a href={job.redirect_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost" style={{ border: "1px solid var(--border)" }}>
              Apply <ExternalLink size={14} />
            </a>
          </div>
        ))}
      </div>
    )}
  </div>
);

const StatusSection = ({ user, apiFetch, setUser }) => {
  const [loading, setLoading] = useState(false);

  const updateStatus = async (newStatus) => {
    setLoading(true);
    try {
      if (newStatus === "unsubscribed") {
        await apiFetch("unsubscribeUser", { user_id: user.user_id });
      } else {
        await apiFetch("toggleUserStatus", { user_id: user.user_id, status: newStatus });
      }
      const password = localStorage.getItem("_pw");
      const updated = await apiFetch("login", { email: user.email, password });
      setUser(updated);
      localStorage.setItem("user", JSON.stringify(updated));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const statusMap = {
    active: { label: "Fully Automated", icon: CheckCircle2, color: "var(--success)", desc: "The engine is currently searching and mailing you jobs daily." },
    paused: { label: "Service Paused", icon: Clock, color: "var(--warning)", desc: "Automation is stopped. Your preferences are saved but no jobs will be processed." },
    unsubscribed: { label: "Unsubscribed", icon: LogOut, color: "var(--danger)", desc: "Account is inactive. You will not receive any further communications." },
    blocked: { label: "System Blocked", icon: AlertCircle, color: "var(--danger)", desc: "Please contact administration regarding your account status." }
  };

  const config = statusMap[user.status?.toLowerCase()] || statusMap.paused;

  return (
    <div className="animate-in card" style={{ maxWidth: "600px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.5rem" }}>
        <div style={{ padding: "1rem", borderRadius: "var(--radius-lg)", background: `rgba(${config.color === 'var(--success)' ? '16, 185, 129' : '239, 68, 68'}, 0.1)`, color: config.color }}>
          <config.icon size={32} />
        </div>
        <div>
          <h3 style={{ marginBottom: "0.25rem" }}>{config.label}</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>{config.desc}</p>
        </div>
      </div>
      
      <div style={{ display: "flex", gap: "1rem", marginTop: "2rem" }}>
        {user.status !== "active" && (
          <button onClick={() => updateStatus("active")} className="btn btn-primary" disabled={loading}>Resume Engine</button>
        )}
        {user.status === "active" && (
          <button onClick={() => updateStatus("paused")} className="btn" style={{ background: "var(--surface-hover)", border: "1px solid var(--border)" }} disabled={loading}>Pause Automation</button>
        )}
        {user.status !== "unsubscribed" && (
          <button onClick={() => updateStatus("unsubscribed")} className="btn-ghost" style={{ color: "var(--danger)" }} disabled={loading}>Unsubscribe</button>
        )}
      </div>
    </div>
  );
};

// --- Helpers ---

const InfoItem = ({ label, value, monospace }) => (
  <div>
    <p style={{ fontSize: "0.75rem", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.4rem" }}>{label}</p>
    <p style={{ fontSize: "0.9375rem", fontFamily: monospace ? "var(--font-mono, monospace)" : "inherit" }}>{value || "—"}</p>
  </div>
);

const StatCard = ({ label, value, icon: Icon, color }) => (
  <div style={{ padding: "1.25rem", background: "var(--bg)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: color, marginBottom: "0.75rem" }}>
      <Icon size={16} />
      <span style={{ fontSize: "0.75rem", fontWeight: "600", textTransform: "uppercase" }}>{label}</span>
    </div>
    <p style={{ fontSize: "1.5rem", fontWeight: "700" }}>{value}</p>
  </div>
);
