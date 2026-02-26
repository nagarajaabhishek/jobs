import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { BrainCircuit, Menu, X } from 'lucide-react';
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
          <Link to="/" style={{ color: !isUni && location.pathname !== '/architecture' ? 'white' : 'var(--text-secondary)' }} className="hover-text-white transition-colors">For Students</Link>
          <Link to="/for-universities" style={{ color: isUni ? 'white' : 'var(--text-secondary)' }} className="hover-text-white transition-colors">For Universities</Link>
          <Link to="/architecture" style={{ color: location.pathname === '/architecture' ? 'white' : 'var(--text-secondary)' }} className="hover-text-white transition-colors">Architecture Engine</Link>
          <button className="btn-secondary" style={{ padding: '8px 16px' }}>Sign In</button>
        </div>

        {/* Mobile Menu Toggle */}
        <button className="mobile-menu-toggle" onClick={toggleMenu}>
          {isOpen ? <X size={28} /> : <Menu size={28} />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      <div className={`mobile-menu-overlay ${isOpen ? 'open' : ''}`}>
        <Link to="/" onClick={closeMenu} className={!isUni && location.pathname !== '/architecture' ? 'active' : ''}>For Students</Link>
        <Link to="/for-universities" onClick={closeMenu} className={isUni ? 'active' : ''}>For Universities</Link>
        <Link to="/architecture" onClick={closeMenu} className={location.pathname === '/architecture' ? 'active' : ''}>Architecture Engine</Link>
        <button className="btn-primary" style={{ width: '100%', marginTop: '20px' }}>Sign In</button>
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

        {/* Shared Footer */}
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
