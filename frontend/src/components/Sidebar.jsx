import { NavLink } from "react-router-dom";

function Sidebar({ dark, setDark }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-title">
        <span>CI/CD</span> Failure Predictor
      </div>
      <nav>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          <span>Dashboard</span>
        </NavLink>
        <NavLink to="/predict" className={({ isActive }) => (isActive ? "active" : "")}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          <span>Predict</span>
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => (isActive ? "active" : "")}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span>History</span>
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <button className="theme-toggle" onClick={() => setDark(!dark)}>
          {dark ? "\u2600\uFE0F" : "\uD83C\uDF19"} <span>{dark ? "Light Mode" : "Dark Mode"}</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
