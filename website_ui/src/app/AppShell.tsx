import { NavLink, Outlet, Link } from 'react-router-dom';
import {
  BrainCircuit,
  LayoutDashboard,
  GitBranch,
  Briefcase,
  FileText,
  UserCircle,
  Settings,
  ExternalLink,
} from 'lucide-react';
import './app.css';

const nav = [
  { to: '/app', label: 'Overview', icon: LayoutDashboard },
  { to: '/app/pipeline', label: 'Pipeline', icon: GitBranch },
  { to: '/app/jobs', label: 'Jobs & evaluation', icon: Briefcase },
  { to: '/app/resume', label: 'Resume & tailor', icon: FileText },
  { to: '/app/context', label: 'Profile context', icon: UserCircle },
  { to: '/app/settings', label: 'Settings', icon: Settings },
] as const;

/**
 * Application chrome for the agent-connected product.
 * Marketing pages use the main site layout; /app/* is the operational hub.
 */
export default function AppShell() {
  return (
    <div className="app-root">
      <div className="app-body">
        <aside className="app-sidebar" aria-label="Application navigation">
          <div className="app-sidebar-brand">
            <Link to="/app">
              <BrainCircuit color="var(--accent-primary)" size={26} />
              <span>
                Thara Ops
                <span className="sub">Job Automation agents</span>
              </span>
            </Link>
          </div>
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/app'}
              className={({ isActive }) => `app-nav-link${isActive ? ' active' : ''}`}
            >
              <Icon size={18} strokeWidth={2} />
              {label}
            </NavLink>
          ))}
          <div className="app-sidebar-footer">
            <a
              href="/"
              className="app-nav-link"
              style={{ padding: '8px 20px', fontSize: '0.85rem' }}
            >
              <ExternalLink size={16} />
              Marketing site
            </a>
          </div>
        </aside>
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
