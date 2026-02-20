import React, { useState } from 'react';
import { BrainCircuit, Briefcase, Network, ArrowRight, CheckCircle2, FileText, Target, Map, Database, GitBranch, BarChart3, GraduationCap, Building2 } from 'lucide-react';
import './index.css';

function App() {
  const [activeResume, setActiveResume] = useState('ba');

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1200px', margin: '0 auto', position: 'relative', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', fontSize: '1.25rem' }}>
          <BrainCircuit color="var(--accent-primary)" size={28} />
          <span>SyllabusSync <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: '500' }}>by Job Automation</span></span>
        </div>
        <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <a href="#students" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: '500' }} className="hover-text-white transition-colors">For Students</a>
          <a href="#universities" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: '500' }} className="hover-text-white transition-colors">For Universities</a>
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
              <CheckCircle2 size={16} /> Beta Exclusive: UT System
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

      {/* Student Section - Feature Grid */}
      <section id="students" className="features-section">
        <div className="container">
          <div className="section-header animate-fade-up">
            <h2 className="text-gradient">The Frictionless Pipeline</h2>
            <p>Most job applications feel like a black hole. We reversed the process by using your actual university curriculum as your moat.</p>
          </div>

          <div className="feature-grid">
            <div className="feature-card animate-fade-up delay-1">
              <div className="feature-icon">
                <Briefcase size={24} />
              </div>
              <h3>1. Centralized Feed</h3>
              <p>Stop hunting across 5 different job boards. We scrape target company career pages every morning. You see the top 100 open roles in one place.</p>
            </div>

            <div className="feature-card animate-fade-up delay-2">
              <div className="feature-icon">
                <BrainCircuit size={24} />
              </div>
              <h3>2. Pre-Evaluated Routing</h3>
              <p>Our background LLM automatically maps new jobs against all of your resume profiles instantly. We tell you exactly which resume yields the highest probability before you click apply.</p>
            </div>

            <div className="feature-card animate-fade-up delay-3">
              <div className="feature-icon">
                <Network size={24} />
              </div>
              <h3>3. Warm Alumni Sourcing</h3>
              <p>You aren't competing against the internet. We specifically source roles from companies with a proven track record of hiring alumni from exactly your university and program.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Technical Breakdown Section */}
      <section className="engine-section">
        <div className="container">
          <div className="engine-grid">
            <div className="engine-text animate-fade-up">
              <h2>How the Engine Works</h2>
              <p className="subtitle">Built on verified intelligence, not keyword spam.</p>

              <div className="engine-steps">
                <div className="engine-step">
                  <div className="step-icon"><Database size={20} /></div>
                  <div className="step-content">
                    <h4>Direct ATS Ingestion</h4>
                    <p>We bypass LinkedIn "ghost jobs" by directly scraping validated openings from Greenhouse, Workday, and Lever.</p>
                  </div>
                </div>

                <div className="engine-step">
                  <div className="step-icon"><GitBranch size={20} /></div>
                  <div className="step-content">
                    <h4>Contextual Syllabus Mapping</h4>
                    <p>Our Tiered LLM Router maps job requirements against verified university course descriptions, preventing hallucinated "matches".</p>
                  </div>
                </div>

                <div className="engine-step">
                  <div className="step-icon"><Map size={20} /></div>
                  <div className="step-content">
                    <h4>Prescriptive Gap Analysis</h4>
                    <p>Instead of generic rejections, we connect missing skills directly to specific university electives required to fill them.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="engine-visual animate-fade-up delay-2">
              <div className="glass-panel">
                <div className="code-header">
                  <span style={{ color: 'var(--accent-primary)' }}>job_evaluation</span><span style={{ color: 'var(--text-secondary)' }}>(student_id)</span>
                </div>
                <div className="code-body">
                  <div className="code-line"><span className="keyword">import</span> <span className="string">syllabus_data</span></div>
                  <div className="code-line"><span className="keyword">const</span> match = <span className="function">analyze_fit</span>(resume_tpm, jd_042)</div>
                  <div className="code-line mt-2 text-warning">{'// Alert: Missing specific keyword: Advanced Scrum'}</div>
                  <div className="code-line"><span className="keyword">const</span> prescriptive_action = <span className="function">resolve_gap</span>('Advanced Scrum')</div>
                  <div className="code-line mt-2 text-success">{'>> Recommendation: Enroll in IE 5301 Spring Semester'}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* University B2B Section */}
      <section id="universities" className="b2b-section">
        <div className="b2b-bg-glow"></div>
        <div className="container">
          <div className="section-header text-center animate-fade-up">
            <div className="b2b-badge">For Universities & Dept Heads</div>
            <h2>Close the "Black Box" of Student Success</h2>
            <p style={{ maxWidth: '700px', margin: '0 auto' }}>Stop guessing why graduates aren't getting hired. Get actionable data to prove your curriculum's ROI.</p>
          </div>

          <div className="b2b-grid">
            <div className="b2b-card animate-fade-up delay-1">
              <BarChart3 size={32} className="b2b-icon" />
              <h3>Actionable Analytics</h3>
              <p>See exactly where your students are failing market demands. E.g., "60% of graduating Engineering Management students lack Agile experience."</p>
            </div>

            <div className="b2b-card animate-fade-up delay-2">
              <Building2 size={32} className="b2b-icon" />
              <h3>Prove Curriculum ROI</h3>
              <p>Gather the data needed to justify syllabus updates. Show how adding a 1-week certification module directly increased local hiring rates.</p>
            </div>

            <div className="b2b-card animate-fade-up delay-3">
              <GraduationCap size={32} className="b2b-icon" />
              <h3>Accreditation Data</h3>
              <p>Generate automated reports for ABET or AACSB accreditation workflows based on verified student skill mastery against real-world job data.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Dual CTA Validation Section */}
      <section className="cta-section">
        <div className="container text-center animate-fade-up">
          <h2>Join the Alpha Cohort</h2>
          <p className="cta-subtext">Currently validating partnerships across the UT System ecosystems.</p>

          <div className="dual-cta-container">
            <div className="cta-box student-cta">
              <GraduationCap size={32} />
              <h3>For Students</h3>
              <p>Stop guessing your applications. Get a pre-evaluated job feed.</p>
              <button className="btn-primary w-full">Request Beta Access</button>
            </div>

            <div className="cta-box uni-cta">
              <Building2 size={32} />
              <h3>For Universities</h3>
              <p>Close the curriculum feedback loop with real placement data.</p>
              <button className="btn-secondary w-full">Request Department Demo</button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', fontSize: '1.25rem', marginBottom: '16px' }}>
              <BrainCircuit color="var(--accent-primary)" size={24} />
              <span>SyllabusSync</span>
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
  );
}

export default App;

