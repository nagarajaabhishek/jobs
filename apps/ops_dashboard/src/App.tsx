import { NavLink, Route, Routes, Navigate, Outlet } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import JobDetail from './pages/JobDetail';
import Resumes from './pages/Resumes';

function Shell() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Job Automation</h1>
        <p className="sub">Ops dashboard — single user (no auth)</p>
        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            Dashboard
          </NavLink>
          <NavLink to="/resumes" className={({ isActive }) => (isActive ? 'active' : '')}>
            Resumes
          </NavLink>
        </nav>
      </aside>
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/job" element={<JobDetail />} />
        <Route path="/resumes" element={<Resumes />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
