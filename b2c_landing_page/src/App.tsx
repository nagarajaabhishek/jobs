import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { BrainCircuit, Menu, X, Github } from 'lucide-react';
import StudentLanding from './pages/StudentLanding';
import UniversityLanding from './pages/UniversityLanding';
import Architecture from './pages/Architecture';
import './index.css';

function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const isUni = location.pathname === '/for-universities';

  const toggleMenu = () => setIsOpen(!isOpen);
  const closeMenu = () => setIsOpen(false);

  return (
    <nav className="nav-container">
      <div className="nav-main">
        <Link to="/" onClick={closeMenu} className="nav-logo">
          <BrainCircuit color="var(--accent-primary)" size={28} />
          <span>JobsProof.com <span className="logo-subtext">by Job Automation</span></span>
        </Link>

        {/* Desktop Links */}
        <div className="nav-links-desktop">
          <Link to="/" style={{ color: !isUni ? 'white' : 'var(--text-secondary)' }} className="hover-text-white transition-colors">For Students</Link>
          <Link to="/for-universities" style={{ color: isUni ? 'white' : 'var(--text-secondary)' }} className="hover-text-white transition-colors">For Universities</Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginLeft: '12px', borderLeft: '1px solid var(--border-color)', paddingLeft: '24px' }}>
            <a href="https://github.com/nagarajaabhishek/jobs" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', transition: 'color 0.2s' }} className="hover-text-white" title="Job Automation Repo">
              <Github size={20} />
            </a>
            <a href="https://github.com/nagarajaabhishek/resume_agent" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', transition: 'color 0.2s' }} className="hover-text-white" title="Resume Agent Repo">
              <Github size={20} />
            </a>
          </div>
        </div>

        {/* Mobile Menu Toggle */}
        <button className="mobile-menu-toggle" onClick={toggleMenu}>
          {isOpen ? <X size={28} /> : <Menu size={28} />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      <div className={`mobile-menu-overlay ${isOpen ? 'open' : ''}`}>
        <Link to="/" onClick={closeMenu} className={!isUni ? 'active' : ''}>For Students</Link>
        <Link to="/for-universities" onClick={closeMenu} className={isUni ? 'active' : ''}>For Universities</Link>
        <div style={{ display: 'flex', gap: '16px', marginTop: '20px', justifyContent: 'center' }}>
          <a href="https://github.com/nagarajaabhishek/jobs" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Github size={24} /> Job Pipeline
          </a>
          <a href="https://github.com/nagarajaabhishek/resume_agent" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Github size={24} /> Resume Agent
          </a>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen">
        <Navigation />

        <main>
          <Routes>
            <Route path="/" element={<StudentLanding />} />
            <Route path="/for-students" element={<StudentLanding />} />
            <Route path="/for-universities" element={<UniversityLanding />} />
            <Route path="/architecture" element={<Architecture />} />
          </Routes>
        </main>

        <footer className="footer">
          <div className="container">
            <div className="footer-content">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', fontSize: '1.25rem', marginBottom: '16px' }}>
                <BrainCircuit color="var(--accent-primary)" size={24} />
                <span>JobsProof.com</span>
              </div>
              <p className="footer-text">Built to eliminate the friction between university curriculums and industry demands.</p>
            </div>
            <div className="footer-bottom">
              <p className="footer-text">© 2026 Job Automation. All rights reserved.</p>
              <div className="footer-links">
                <a href="https://github.com/nagarajaabhishek/jobs" target="_blank" rel="noopener noreferrer">Job Automation Repo</a>
                <a href="https://github.com/nagarajaabhishek/resume_agent" target="_blank" rel="noopener noreferrer">Resume Agent Repo</a>
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
              </div>
            </div>
          </div>
        </footer>

      </div>
    </Router>
  );
}

export default App;
