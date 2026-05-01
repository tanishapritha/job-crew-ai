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
  DollarSign,
  ArrowRight,
  ShieldCheck,
  Zap,
  Globe,
  Mail,
  Menu,
  X
} from "lucide-react";

const API_URL = "https://tanishapritha-job-crew.hf.space";

// --- Components ---

const ThemeToggle = ({ theme, toggleTheme }) => (
  <button onClick={toggleTheme} className="btn-theme" title="Toggle theme">
    {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
  </button>
);

const Badge = ({ variant, children }) => {
  const v = variant?.toLowerCase();
  const style = v === 'linkedin' ? 'badge-linkedin' : v === 'indeed' ? 'badge-indeed' : 'badge-other';
  return <span className={`badge ${style}`}>{children}</span>;
};

// --- App ---

export default function App() {
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "dark");
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("user")) || null);
  const [view, setView] = useState(user ? "dashboard" : "auth"); // auth, dashboard
  const [screen, setScreen] = useState("profile"); // profile, preferences, jobs, status
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
    setView("auth");
  };

  const handleLoginSuccess = (profile) => {
    setUser(profile);
    setView("dashboard");
  };

  return (
    <div className={`app-wrapper ${theme}`}>
      {view === "auth" && (
        <AuthScreen 
          onSuccess={handleLoginSuccess}
          apiFetch={apiFetch} 
          theme={theme} 
          toggleTheme={toggleTheme}
        />
      )}

      {view === "dashboard" && (
        <div className="app-container animate-fade">
          <Sidebar 
            current={screen} 
            setScreen={setScreen} 
            onLogout={handleLogout} 
            user={user}
            theme={theme}
            toggleTheme={toggleTheme}
          />
          <main className="main-content">
            <Header user={user} screen={screen} setView={setView} />
              {user.isAdmin ? (
                <AdminDashboard apiFetch={apiFetch} />
              ) : (
                <>
                  {screen === "profile" && <ProfileSection user={user} />}
                  {screen === "preferences" && <PreferencesSection user={user} apiFetch={apiFetch} setUser={setUser} setJobs={setJobs} setScreen={setScreen} />}
                  {screen === "jobs" && <JobsSection jobs={jobs} />}
                  {screen === "status" && <StatusSection user={user} apiFetch={apiFetch} setUser={setUser} />}
                </>
              )}
            </div>
            {error && <div className="error-banner card"><AlertCircle size={16} /> {error}</div>}
          </main>
        </div>
      )}
    </div>
  );
}

// --- Auth Section ---

const AuthScreen = ({ onSuccess, apiFetch, theme, toggleTheme }) => {
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
      
      let profile;
      try {
        profile = await apiFetch("login", { email: formData.email, password: formData.password });
      } catch (loginErr) {
        // If normal login fails, try admin login
        profile = await apiFetch("adminLogin", { email: formData.email, password: formData.password });
      }
      
      localStorage.setItem("user", JSON.stringify(profile));
      localStorage.setItem("_pw", formData.password);
      onSuccess(profile);
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container animate-fade">
      <div className="card animate-up" style={{ width: "100%", maxWidth: "420px", padding: "2.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontWeight: "800", fontSize: "1.25rem" }}>
            <Briefcase size={24} color="#3b82f6" strokeWidth={3} />
            Job Engine
          </div>
          <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
        </div>
        
        <div style={{ marginBottom: "2rem" }}>
          <h2 style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>{isRegister ? "Join the Force" : "Sign In"}</h2>
          <p style={{ color: "var(--text-muted)" }}>{isRegister ? "Start your automated job hunt in minutes." : "Access your autonomous search dashboard."}</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {isRegister && (
            <div className="input-group">
              <label>Full Name</label>
              <input type="text" placeholder="Jane Doe" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
            </div>
          )}
          <div className="input-group">
            <label>Email Address</label>
            <input type="email" placeholder="jane@example.com" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} required />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input type="password" placeholder="••••••••" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} required />
          </div>
          {localError && <p style={{ color: "var(--danger)", fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "0.4rem" }}><AlertCircle size={14}/> {localError}</p>}
          <button type="submit" className="btn btn-primary" style={{ marginTop: "0.5rem", width: "100%", height: "48px" }} disabled={loading}>
            {loading ? "Processing..." : (isRegister ? "Create Account" : "Sign In to Dashboard")}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "2rem", fontSize: "0.875rem", color: "var(--text-muted)" }}>
          {isRegister ? "Already have an account?" : "New to the engine?"} {" "}
          <button className="btn-link" style={{ color: "var(--primary)", fontWeight: "600", border: "none", background: "none", cursor: "pointer" }} onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? "Sign In" : "Register Free"}
          </button>
        </p>
      </div>
    </div>
  );
};

// --- Dashboard Sections ---

const Sidebar = ({ current, setScreen, onLogout, user, theme, toggleTheme }) => {
  const navItems = user?.isAdmin ? [
    { id: "admin", label: "Admin Dashboard", icon: Activity }
  ] : [
    { id: "profile", label: "My Profile", icon: User },
    { id: "preferences", label: "Job Preferences", icon: Settings },
    { id: "jobs", label: "Job Results", icon: Briefcase },
    { id: "status", label: "Service Health", icon: Activity },
  ];

  return (
    <aside className="sidebar card" style={{ height: "100vh", position: "sticky", top: 0, borderRadius: 0, borderTop: "none", borderBottom: "none", width: "280px", display: "flex", flexDirection: "column", padding: 0 }}>
      <div style={{ padding: "2rem", borderBottom: "1px solid var(--border)" }}>
        <h2 style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "1.25rem", color: "var(--text)" }}>
          <Briefcase size={26} color="var(--primary)" strokeWidth={2.5} />
          JobEngine
        </h2>
      </div>
      
      <nav style={{ padding: "1.5rem", flex: 1 }}>
        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {navItems.map(item => (
            <li key={item.id}>
              <button 
                onClick={() => setScreen(item.id)}
                className="btn"
                style={{ 
                  width: "100%", 
                  justifyContent: "flex-start",
                  background: current === item.id ? "rgba(37, 99, 235, 0.08)" : "transparent",
                  color: current === item.id ? "var(--primary)" : "var(--text-muted)",
                  padding: "0.875rem 1.25rem",
                  border: "none"
                }}
              >
                <item.icon size={20} strokeWidth={current === item.id ? 2.5 : 2} />
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div style={{ padding: "1.5rem", borderTop: "1px solid var(--border)", display: "flex", gap: "1rem", alignItems: "center" }}>
        <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
        <button onClick={onLogout} className="btn-ghost" style={{ color: "var(--danger)", marginLeft: "auto" }} title="Logout">
          <LogOut size={20} />
        </button>
      </div>
    </aside>
  );
};

const Header = ({ user, screen, setView }) => {
  const titles = user?.isAdmin ? {
    admin: "Admin Dashboard",
    profile: "Admin Dashboard"
  } : {
    profile: "My Profile",
    preferences: "Job Preferences",
    jobs: "Job Results",
    status: "Service Health"
  };

  return (
    <header style={{ marginBottom: "2.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div>
        <h1 style={{ fontSize: "1.75rem", fontWeight: "800", letterSpacing: "-0.02em" }}>{titles[screen]}</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>{user.email}</p>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
         <div style={{ textAlign: "right" }}>
            <p style={{ fontSize: "0.875rem", fontWeight: "700" }}>{user.name}</p>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{user.status}</p>
         </div>
         <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "var(--primary)", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "700" }}>
            {user.name[0]}
         </div>
      </div>
    </header>
  );
};

// --- Nested Pages ---

const ProfileSection = ({ user }) => (
  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "2rem" }}>
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <User size={20} color="var(--primary)" />
        <h3 style={{ fontSize: "1.25rem" }}>Identity Details</h3>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <InfoItem label="Legal Name" value={user.name} />
        <InfoItem label="Primary Email" value={user.email} />
        <InfoItem label="Account Reference" value={user.user_id} monospace />
      </div>
    </div>
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <ShieldCheck size={20} color="var(--success)" />
        <h3 style={{ fontSize: "1.25rem" }}>Usage Limits</h3>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <StatCard label="Emails Dispatched" value={user.emails_sent || 0} icon={Mail} color="var(--primary)" />
        <StatCard label="Daily Hunt Cap" value={user.daily_limit || 25} icon={Zap} color="var(--warning)" />
      </div>
    </div>
  </div>
);

const AdminDashboard = ({ apiFetch }) => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    apiFetch("getSystemStats").then(setStats).catch(console.error);
  }, []);

  if (!stats) return <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Loading stats...</div>;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1.5rem" }}>
      <StatCard label="Total Users" value={stats.total_users} icon={User} color="var(--primary)" />
      <StatCard label="Active Users" value={stats.active_users} icon={Zap} color="var(--success)" />
      <StatCard label="Paused Users" value={stats.paused_users} icon={Clock} color="var(--warning)" />
      <StatCard label="Emails Sent" value={stats.total_emails_sent} icon={Mail} color="var(--primary)" />
    </div>
  );
};

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
    <div className="card">
      <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
        <div className="input-group">
          <label style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            Target Domains
            <span style={{ fontSize: "0.75rem", fontWeight: "normal", color: "var(--text-muted)" }}>Use semicolons to separate different job titles</span>
          </label>
          <input 
            type="text" 
            placeholder="Flutter Developer; UX Designer; Product Manager" 
            value={prefs.domains} 
            onChange={e => setPrefs({...prefs, domains: e.target.value})}
            style={{ fontWeight: "500" }}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1.25rem" }}>
          <div className="input-group">
            <label>Priority Location</label>
            <input type="text" placeholder="London, UK" value={prefs.location_1} onChange={e => setPrefs({...prefs, location_1: e.target.value})} />
          </div>
          <div className="input-group">
            <label>Secondary Location</label>
            <input type="text" placeholder="Remote, EU" value={prefs.location_2} onChange={e => setPrefs({...prefs, location_2: e.target.value})} />
          </div>
          <div className="input-group">
            <label>Tertiary Location</label>
            <input type="text" placeholder="San Francisco, US" value={prefs.location_3} onChange={e => setPrefs({...prefs, location_3: e.target.value})} />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "2rem", alignItems: "center" }}>
          <div className="input-group">
            <label>Experience Tier</label>
            <select value={prefs.experience_level} onChange={e => setPrefs({...prefs, experience_level: e.target.value})}>
              <option value="beginner">Early Career (0-2y)</option>
              <option value="intermediate">Mid-Level (3-5y)</option>
              <option value="senior">Senior / Lead (6y+)</option>
            </select>
          </div>
          <div className="input-group">
            <label>Minimum Salary (Yearly)</label>
            <input type="number" placeholder="85,000" value={prefs.min_salary} onChange={e => setPrefs({...prefs, min_salary: e.target.value})} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", paddingTop: "1.5rem" }}>
            <input 
              type="checkbox" 
              id="remote_hunt" 
              checked={prefs.remote_jobs} 
              onChange={e => setPrefs({...prefs, remote_jobs: e.target.checked})} 
              style={{ width: "20px", height: "20px", accentColor: "var(--primary)" }}
            />
            <label htmlFor="remote_hunt" style={{ fontWeight: "600", cursor: "pointer", fontSize: "0.9375rem" }}>Include Remote Roles</label>
          </div>
        </div>

        <div style={{ padding: "2rem", border: "1px dashed var(--border)", borderRadius: "var(--radius-md)", display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(37, 99, 235, 0.02)" }}>
          <div>
            <h4 style={{ marginBottom: "0.25rem" }}>Save and get everyday mails</h4>
            <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>Save these settings to the daily automation engine.</p>
          </div>
          <div style={{ display: "flex", gap: "1rem" }}>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Deploying..." : "Save Preferences"}
            </button>
            <button type="button" onClick={handleSearchNow} className="btn btn-secondary" disabled={saving}>
              <Search size={18} /> Instant Search
            </button>
          </div>
        </div>
        {success && <p style={{ color: "var(--success)", fontWeight: "600", textAlign: "center", marginTop: "-1rem" }}>✓ Settings synchronised successfully</p>}
      </form>

      <div style={{ marginTop: "4rem", paddingTop: "3rem", borderTop: "1px solid var(--border)", maxWidth: "500px", margin: "4rem auto 0" }}>
        <h3 style={{ fontSize: "1rem", marginBottom: "1.5rem", textAlign: "center", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em" }}>Autonomous Engine Active</h3>
        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <li style={{ display: "flex", gap: "1rem", fontSize: "0.875rem" }}>
            <span style={{ color: "var(--success)", fontWeight: "bold" }}>✓</span>
            <div>
               <strong style={{ display: "block", marginBottom: "0.25rem" }}>Global Discovery</strong>
               <span style={{ color: "var(--text-muted)" }}>Concurrent monitoring of LinkedIn, Indeed, Glassdoor and Adzuna for maximum coverage.</span>
            </div>
          </li>
          <li style={{ display: "flex", gap: "1rem", fontSize: "0.875rem" }}>
            <span style={{ color: "var(--success)", fontWeight: "bold" }}>✓</span>
            <div>
               <strong style={{ display: "block", marginBottom: "0.25rem" }}>Agentic Filtering</strong>
               <span style={{ color: "var(--text-muted)" }}>An AI Researcher reads every description to verify seniority and salary match before you see it.</span>
            </div>
          </li>
          <li style={{ display: "flex", gap: "1rem", fontSize: "0.875rem" }}>
            <span style={{ color: "var(--success)", fontWeight: "bold" }}>✓</span>
            <div>
               <strong style={{ display: "block", marginBottom: "0.25rem" }}>Daily Delivery</strong>
               <span style={{ color: "var(--text-muted)" }}>A curated PDF-style HTML digest delivered to your inbox every morning at 9:00 AM.</span>
            </div>
          </li>
        </ul>
      </div>
    </div>
  );
};

const JobsSection = ({ jobs }) => (
  <div className="jobs-container">
    {!jobs || jobs.length === 0 ? (
      <div className="card" style={{ textAlign: "center", padding: "6rem 2rem", background: "transparent", borderStyle: "dashed" }}>
        <Briefcase size={56} style={{ color: "var(--border)", marginBottom: "1.5rem" }} />
        <h3 style={{ marginBottom: "0.5rem" }}>No active leads</h3>
        <p style={{ color: "var(--text-muted)", maxWidth: "400px", margin: "0 auto" }}>Go to **Hunt Settings** and click **Instant Search** to populate this area with live market data.</p>
      </div>
    ) : (
      <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem", alignItems: "baseline" }}>
           <p style={{ fontWeight: "700", color: "var(--text-muted)" }}>{jobs.length} Opportunities Identified</p>
           <p style={{ fontSize: "0.8125rem", color: "var(--primary)" }}>Filtered by AI Researcher Agent</p>
        </div>
        {jobs.map((job, idx) => (
          <div key={idx} className="card job-item animate-up" style={{ animationDelay: `${idx * 0.05}s`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ flex: 1, minWidth: 0, paddingRight: "2rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.75rem" }}>
                <h4 style={{ fontSize: "1.125rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{job.title}</h4>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <Badge variant={job.source}>{job.source}</Badge>
                  {job.matched_domain && <span style={{ fontSize: "0.625rem", textTransform: "uppercase", background: "var(--surface-hover)", padding: "2px 8px", borderRadius: "4px", color: "var(--text-muted)", fontWeight: "700" }}>{job.matched_domain}</span>}
                </div>
              </div>
              <div style={{ display: "flex", gap: "2rem", color: "var(--text-muted)", fontSize: "0.875rem" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><Building2 size={16}/> {job.company}</span>
                <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><MapPin size={16}/> {job.location}</span>
                {job.salary && <span style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--success)" }}><DollarSign size={16}/> {job.salary}</span>}
              </div>
            </div>
            <a href={job.redirect_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ borderRadius: "100px", padding: "0.625rem 1.5rem" }}>
              Apply <ExternalLink size={16} />
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
    active: { label: "Fully Automated", icon: Zap, color: "var(--primary)", desc: "The engine is currently performing exhaustive job hunts and mailing you results daily." },
    paused: { label: "Engine Paused", icon: Clock, color: "var(--warning)", desc: "Automation is on standby. Your preferences are saved, but no active searches are performed." },
    unsubscribed: { label: "Terminated", icon: X, color: "var(--danger)", desc: "Account is inactive. You will not receive any further communications or automated searches." }
  };

  const config = statusMap[user.status?.toLowerCase()] || statusMap.paused;

  return (
    <div className="card" style={{ maxWidth: "650px" }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: "1.5rem", marginBottom: "2.5rem" }}>
        <div style={{ padding: "1.25rem", borderRadius: "18px", background: "rgba(37, 99, 235, 0.1)", color: "var(--primary)" }}>
          <config.icon size={36} strokeWidth={2.5} />
        </div>
        <div>
          <h3 style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>{config.label}</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "1.0625rem", lineHeight: "1.5" }}>{config.desc}</p>
        </div>
      </div>
      
      <div style={{ display: "flex", gap: "1rem", borderTop: "1px solid var(--border)", paddingTop: "2rem" }}>
        {user.status !== "active" && (
          <button onClick={() => updateStatus("active")} className="btn btn-primary" style={{ padding: "0.75rem 2rem" }} disabled={loading}>Resume Engine</button>
        )}
        {user.status === "active" && (
          <button onClick={() => updateStatus("paused")} className="btn btn-secondary" style={{ padding: "0.75rem 2rem" }} disabled={loading}>Pause Hunt</button>
        )}
        {user.status !== "unsubscribed" && (
          <button onClick={() => updateStatus("unsubscribed")} className="btn-ghost" style={{ color: "var(--danger)", fontWeight: "600" }} disabled={loading}>Delete Integration</button>
        )}
      </div>
    </div>
  );
};

// --- Helpers ---

const InfoItem = ({ label, value, monospace }) => (
  <div>
    <p style={{ fontSize: "0.75rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.5rem" }}>{label}</p>
    <p style={{ fontSize: "1.0625rem", fontWeight: "500", fontFamily: monospace ? "'SF Mono', monospace" : "inherit", color: "var(--text)" }}>{value || "—"}</p>
  </div>
);

const StatCard = ({ label, value, icon: Icon, color }) => (
  <div style={{ padding: "1.5rem", background: "rgba(37, 99, 235, 0.03)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
    <div style={{ display: "flex", alignItems: "center", gap: "0.625rem", color: color, marginBottom: "1rem" }}>
      <Icon size={18} strokeWidth={2.5} />
      <span style={{ fontSize: "0.75rem", fontWeight: "800", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</span>
    </div>
    <p style={{ fontSize: "2rem", fontWeight: "800", letterSpacing: "-0.04em" }}>{value}</p>
  </div>
);
