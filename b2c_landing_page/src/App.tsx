import React, { useState } from 'react';
import { BrainCircuit, Briefcase, Network, ArrowRight, CheckCircle2, FileText, Target, Map } from 'lucide-react';
import './index.css';

function App() {
  const [activeResume, setActiveResume] = useState('ba');

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', fontSize: '1.25rem' }}>
          <BrainCircuit color="var(--accent-primary)" size={28} />
          <span>SyllabusSync <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: '500' }}>by Job Automation</span></span>
        </div>
        <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <a href="#how" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: '500' }}>How it Works</a>
          <button className="btn-secondary" style={{ padding: '8px 16px' }}>Sign In</button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-bg-glow"></div>
        <div className="container hero-grid">

          {/* Left: Copy */}
          <div className="hero-content animate-fade-up">
            <div className="student-tag">
              <CheckCircle2 size={16} /> Beta Exclusive: UT System Students
            </div>
            <h1>Stop Guessing.<br /><span className="text-gradient">Start Interviewing.</span></h1>
            <p>The only job feed that instantly tells you if you're a fit, exactly which of your resumes to use, and who hired your classmates last year. Zero text copying required.</p>

            <div className="cta-group">
              <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                View Your Daily Feed <ArrowRight size={18} />
              </button>
              <button className="btn-secondary">Watch Demo</button>
            </div>
          </div>

          {/* Right: The Product UI Mockup */}
          <div className="app-mockup animate-fade-up delay-2">
            <div className="mockup-header">
              <div className="dot dot-r"></div>
              <div className="dot dot-y"></div>
              <div className="dot dot-g"></div>
            </div>

            <div className="mockup-body">
              {/* Fake Sidebar of Resumes */}
              <div className="mockup-sidebar">
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '8px', textTransform: 'uppercase' }}>
                  Context Profiles
                </div>
                <div
                  className={`resume-file ${activeResume === 'tpm' ? 'active' : ''}`}
                  onClick={() => setActiveResume('tpm')}
                  style={{ cursor: 'pointer' }}
                >
                  <FileText size={16} /> role_tpm.yaml
                </div>
                <div
                  className={`resume-file ${activeResume === 'ba' ? 'active' : ''}`}
                  onClick={() => setActiveResume('ba')}
                  style={{ cursor: 'pointer' }}
                >
                  <FileText size={16} /> role_ba.yaml
                </div>
                <div
                  className={`resume-file ${activeResume === 'manager' ? 'active' : ''}`}
                  onClick={() => setActiveResume('manager')}
                  style={{ cursor: 'pointer' }}
                >
                  <FileText size={16} /> role_manager.yaml
                </div>
              </div>

              {/* Fake Main Feed */}
              <div className="mockup-main">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
                  <h3 style={{ fontSize: '1.1rem' }}>Today's "Warm" Targets</h3>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Updated 2h ago</span>
                </div>

                {/* Job Card 1 - The High Match */}
                <div className="job-card" style={{ borderLeft: '4px solid var(--success)' }}>
                  <div className="job-header">
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <div className="company-logo">T</div>
                      <div>
                        <div className="job-title">Product Owner - Digital</div>
                        <div className="job-meta">Toyota NA • Plano, TX</div>
                      </div>
                    </div>
                    <div className="match-badge">
                      <CheckCircle2 size={14} /> 94% Verified Match
                    </div>
                  </div>

                  <div className="action-bar">
                    <div className="routing-advice">
                      <BrainCircuit size={16} color="var(--accent-primary)" />
                      <span>Route: <strong>Use role_ba.yaml</strong> via IE 5301</span>
                    </div>
                    <button className="mock-btn">Apply Now</button>
                  </div>
                </div>

                {/* Job Card 2 - The Gap Analysis */}
                <div className="job-card" style={{ borderLeft: '4px solid var(--warning)', opacity: 0.8 }}>
                  <div className="job-header">
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <div className="company-logo" style={{ background: '#0072C6', color: 'white' }}>M</div>
                      <div>
                        <div className="job-title">Technical Program Manager</div>
                        <div className="job-meta">Microsoft • Irving, TX</div>
                      </div>
                    </div>
                    <div className="match-badge" style={{ background: 'rgba(245, 158, 11, 0.1)', color: 'var(--warning)' }}>
                      <Target size={14} /> Gap Identified
                    </div>
                  </div>

                  <div className="action-bar">
                    <div className="routing-advice text-secondary">
                      <Map size={16} color="var(--warning)" />
                      <span>Missing: <strong>Advanced Scrum</strong>. Take Course 4002.</span>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Feature Grid based on USP Document */}
      <section id="how" className="features-section">
        <div className="container">
          <div className="section-header animate-fade-up delay-1">
            <h2>The Frictionless Pipeline</h2>
            <p>Most job applications feel like a black hole. We reversed the process by using your actual university curriculum as your moat.</p>
          </div>

          <div className="feature-grid">
            <div className="feature-card animate-fade-up delay-1">
              <div className="feature-icon">
                <Briefcase size={24} />
              </div>
              <h3>Centralized Feed</h3>
              <p>Stop hunting across 5 different job boards. We scrape target company career pages every morning. You see the top 100 open roles in one place.</p>
            </div>

            <div className="feature-card animate-fade-up delay-2">
              <div className="feature-icon">
                <BrainCircuit size={24} />
              </div>
              <h3>Pre-Evaluated Routing</h3>
              <p>Our background LLM automatically maps new jobs against all of your resume profiles instantly. We tell you exactly which resume yields the highest probability before you click apply.</p>
            </div>

            <div className="feature-card animate-fade-up delay-3">
              <div className="feature-icon">
                <Network size={24} />
              </div>
              <h3>Warm Alumni Sourcing</h3>
              <p>You aren't competing against the internet. We specifically source roles from companies with a proven track record of hiring alumni from exactly your university and program.</p>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}

export default App;
