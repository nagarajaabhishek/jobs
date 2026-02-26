import { useState, useEffect } from 'react';
import { BrainCircuit, Briefcase, Network, ArrowRight, CheckCircle2, FileText, Target, Map, Database, GitBranch, GraduationCap, Github } from 'lucide-react';
import { Link } from 'react-router-dom';
import DetailedCompetitiveMatrix from '../components/DetailedCompetitiveMatrix';
import FAQ from '../components/FAQ';
import ArchitectureSection from '../components/ArchitectureSection';

export default function StudentLanding() {
    useEffect(() => {
        document.title = "JobsProof.com | Institutional-Grade Career Validation";
    }, []);

    const [activeResume, setActiveResume] = useState('ba');

    return (
        <>
            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-bg-glow"></div>
                <div className="container hero-grid">

                    {/* Left: Copy */}
                    <div className="hero-content animate-fade-up" style={{ width: '100%', maxWidth: '540px', zIndex: 10 }}>
                        <div className="student-tag">
                            <CheckCircle2 size={16} /> Beta Exclusive: UT System
                        </div>
                        <h1 style={{ fontSize: '3.2rem', lineHeight: '1.15', marginBottom: '1.25rem' }}>
                            <span style={{ whiteSpace: 'nowrap' }}>Stop Guessing.</span><br />
                            <span className="text-gradient" style={{ whiteSpace: 'nowrap' }}>Start Interviewing.</span>
                        </h1>

                        <div className="problem-statement" style={{ background: 'rgba(245, 158, 11, 0.05)', borderLeft: '3px solid var(--warning)', padding: '12px 16px', borderRadius: '0 8px 8px 0', marginBottom: '20px' }}>
                            <strong style={{ color: 'var(--warning)', display: 'block', marginBottom: '4px', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>The Problem</strong>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.4' }}>Blindly firing generic resumes into the ATS black hole alongside thousands of applicants, only to get ghosted.</span>
                        </div>

                        <p>Don't just apply anywhere. Target the right roles and tailor your resume for success. <strong>JobsProof.com</strong> validates your background so you only apply to high-match roles.</p>

                        <div className="cta-group" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                            <Link to="/architecture" style={{ textDecoration: 'none' }}>
                                <button
                                    className="btn-primary"
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    Architecture Engine <ArrowRight size={18} />
                                </button>
                            </Link>
                            <a href="https://github.com/nagarajaabhishek/jobs" target="_blank" rel="noopener noreferrer" className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}>
                                <Github size={18} /> Job Automation
                            </a>
                            <a href="https://github.com/nagarajaabhishek/resume_agent" target="_blank" rel="noopener noreferrer" className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}>
                                <Github size={18} /> Resume Agent
                            </a>
                        </div>
                    </div>

                    {/* Right: The Product UI Mockup */}
                    <div className="app-mockup animate-fade-up delay-2" style={{ width: '100%', minWidth: '550px', maxWidth: '650px', transform: 'perspective(1000px) rotateY(-5deg) scale(1.05)', transformOrigin: 'right center' }}>
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
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
                                        <span style={{ color: 'var(--success)', fontSize: '0.75rem', fontWeight: '600' }}>● DIRECT ATS SCRAPE</span>
                                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Verified Active 4h ago</span>
                                    </div>
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
                                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                                            <div className="match-badge">
                                                <CheckCircle2 size={14} /> 94% Verified Match
                                            </div>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--success)', background: 'rgba(16, 185, 129, 0.1)', padding: '2px 8px', borderRadius: '4px', fontWeight: '600' }}>
                                                VISA SPONSORSHIP: YES
                                            </div>
                                        </div>
                                    </div>

                                    <div className="action-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div className="routing-advice">
                                            <BrainCircuit size={16} color="var(--accent-primary)" />
                                            <span>Route: <strong>Use role_ba.yaml</strong></span>
                                        </div>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                <FileText size={14} /> Generate .pdf
                                            </button>
                                            <button className="mock-btn">Auto-Apply</button>
                                        </div>
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
                                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                                            <div className="match-badge" style={{ background: 'rgba(245, 158, 11, 0.1)', color: 'var(--warning)' }}>
                                                <Target size={14} /> Gap Identified
                                            </div>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', background: 'rgba(255, 255, 255, 0.05)', padding: '2px 8px', borderRadius: '4px', fontWeight: '500' }}>
                                                U.S. CITIZEN REQUIRED
                                            </div>
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
            <section className="features-section">
                <div className="container">
                    <div className="section-header animate-fade-up">
                        <h2 className="text-gradient">The Frictionless Pipeline</h2>
                        <p>Most job applications feel like a black hole. We reversed the process by using your actual university curriculum, projects, and proof of work as your competitive moat.</p>
                    </div>

                    <div className="feature-grid">
                        <div className="feature-card animate-fade-up delay-1">
                            <div className="feature-icon">
                                <Briefcase size={24} />
                            </div>
                            <h3>1. Centralized Multi-Source Feed</h3>
                            <p>Stop hunting across isolated job boards. We aggregate and validate open roles from LinkedIn, Indeed, Jobright, and direct ATS pages (Greenhouse, Workday, Lever)—with advanced Dice MCP integration coming soon. You see the top matched roles in one place.</p>
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
                                <FileText size={24} />
                            </div>
                            <h3>3. AI Resume Engineering</h3>
                            <p>We decouple your raw data from design. Our LaTeX Engine dynamically generates a pixel-perfect, ATS-optimized PDF resume tailored specifically to the job you are looking at—enforcing the Google XYZ formula for every bullet point.</p>
                        </div>

                        <div className="feature-card animate-fade-up delay-4">
                            <div className="feature-icon">
                                <Network size={24} />
                            </div>
                            <h3>4. Warm Alumni Sourcing</h3>
                            <p>You aren't competing against the internet. We specifically source roles from companies with a proven track record of hiring alumni from exactly your university and program.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Phase-Based Competitive Analysis */}
            <section className="competitive-section">
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2>The 5-Phase Automation Architecture</h2>
                        <p className="subtitle" style={{ maxWidth: '700px', margin: '0 auto' }}>Students are forced to string together multiple fragmented tools just to get an interview. We combined every phase into one seamless platform powered by agentic intelligence.</p>
                    </div>

                    <div className="phase-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
                        {/* Phase 1: Abstraction */}
                        <div className="phase-card animate-fade-up delay-1">
                            <div className="phase-header">
                                <span className="phase-number">1</span>
                                <h3>Master Context Assembly</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Trying to squeeze your entire life into a 1-page PDF and losing all the rich details of what you actually built.</div>
                                    <div className="tool-tags">
                                        <span className="tool-tag">Word</span>
                                        <span className="tool-tag">1-Page PDF</span>
                                    </div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">JobsProof AI</div>
                                    <div className="way-content">We ingest your <strong>entire context</strong>—school syllabi, projects, and hackathons—into a massive profile used to dynamically build resumes.</div>
                                </div>
                            </div>
                        </div>

                        {/* Phase 2: Sourcing */}
                        <div className="phase-card animate-fade-up delay-2">
                            <div className="phase-header">
                                <span className="phase-number">2</span>
                                <h3>Signal Filtering</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Endless scrolling through noisy feeds, guessing if a company sponsors visas or hires juniors.</div>
                                    <div className="tool-tags">
                                        <span className="tool-tag">LinkedIn</span>
                                        <span className="tool-tag">Indeed</span>
                                    </div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">JobsProof AI</div>
                                    <div className="way-content">An intelligent "Sniffer" pre-screens thousands of jobs, destroying irrelevant roles before you ever see them.</div>
                                </div>
                            </div>
                        </div>

                        {/* Phase 3: Evaluation */}
                        <div className="phase-card animate-fade-up delay-3">
                            <div className="phase-header">
                                <span className="phase-number">3</span>
                                <h3>Context-Aware Evaluation</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Blindly applying and hoping your generic resume passes the ATS keyword parser.</div>
                                    <div className="tool-tags">
                                        <span className="tool-tag">Guesswork</span>
                                        <span className="tool-tag">Rejection</span>
                                    </div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">JobsProof AI</div>
                                    <div className="way-content">We analyze sourced JDs against your <strong>full context</strong>, scoring the exact match and proving why your projects fit the role perfectly.</div>
                                </div>
                            </div>
                        </div>

                        {/* Phase 4: Analytics */}
                        <div className="phase-card animate-fade-up delay-4">
                            <div className="phase-header">
                                <span className="phase-number">4</span>
                                <h3>Market Analytics</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Not knowing why you're getting rejected or what skills employers actually want today.</div>
                                    <div className="tool-tags">
                                        <span className="tool-tag">Blind Spots</span>
                                        <span className="tool-tag">Stagnation</span>
                                    </div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">JobsProof AI</div>
                                    <div className="way-content">Our system learns continuously, harvesting skill gaps and verified H1B sponsor lists to improve daily.</div>
                                </div>
                            </div>
                        </div>

                        {/* Phase 5: Artifact Execution */}
                        <div className="phase-card animate-fade-up delay-5">
                            <div className="phase-header">
                                <span className="phase-number">5</span>
                                <h3>Artifact Execution</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Submitting the exact same vanilla Word Document to every single job, regardless of the unique requirements.</div>
                                    <div className="tool-tags">
                                        <span className="tool-tag">Generic PDFs</span>
                                    </div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">JobsProof AI</div>
                                    <div className="way-content">We trigger a <strong>Python LaTeX Engine</strong> that algorithmically compiles a bespoke, 90%+ ATS-optimized resume injected with the exact missing keywords.</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Detailed Competitive Matrix */}
            <DetailedCompetitiveMatrix />

            {/* Alumni Network Section */}
            <section className="alumni-section">
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient">The Alumni Intelligence Network</h2>
                        <p className="subtitle" style={{ maxWidth: '800px', margin: '0 auto' }}>
                            Stop cold-DMing strangers on LinkedIn. We map exactly where your program's alumni were hired, their starting roles, and the exact "Verified Match" score they used to get in.
                        </p>
                    </div>

                    <div className="alumni-grid">
                        <div className="alumni-card animate-fade-up delay-1">
                            <div className="alumni-badge">UTD MSITM '25</div>
                            <div className="alumni-content">
                                <h4>Business Analyst</h4>
                                <p>Toyota North America</p>
                                <div className="alumni-stats">
                                    <span className="stat"><CheckCircle2 size={12} /> 96% Match</span>
                                    <span className="stat"><Database size={12} /> IE 5301 Context</span>
                                </div>
                            </div>
                        </div>

                        <div className="alumni-card animate-fade-up delay-2">
                            <div className="alumni-badge">UTD CS '24</div>
                            <div className="alumni-content">
                                <h4>Software Engineer</h4>
                                <p>JPMorgan Chase & Co.</p>
                                <div className="alumni-stats">
                                    <span className="stat"><CheckCircle2 size={12} /> 92% Match</span>
                                    <span className="stat"><GitBranch size={12} /> Hackathon Win</span>
                                </div>
                            </div>
                        </div>

                        <div className="alumni-card animate-fade-up delay-3">
                            <div className="alumni-badge">UTD BUAN '25</div>
                            <div className="alumni-content">
                                <h4>Data Scientist</h4>
                                <p>Capital One</p>
                                <div className="alumni-stats">
                                    <span className="stat"><CheckCircle2 size={12} /> 94% Match</span>
                                    <span className="stat"><Target size={12} /> Capstone Proof</span>
                                </div>
                            </div>
                        </div>

                        <div className="alumni-card animate-fade-up delay-4">
                            <div className="alumni-badge">UTD MBA '24</div>
                            <div className="alumni-content">
                                <h4>Product Manager</h4>
                                <p>Dell Technologies</p>
                                <div className="alumni-stats">
                                    <span className="stat"><CheckCircle2 size={12} /> 89% Match</span>
                                    <span className="stat"><Briefcase size={12} /> Industry Cert</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style={{ textAlign: 'center', marginTop: '40px' }} className="animate-fade-up">
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px' }}>
                            Join 400+ students from your university already using curriculum-backed data.
                        </p>
                        <button className="btn-secondary">View All Alumni Placements</button>
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
                                        <h4>Direct ATS & Multi-Board Ingestion</h4>
                                        <p>We bypass "ghost jobs" by validating openings across LinkedIn, Indeed, and Jobright, alongside direct ATS feeds from Greenhouse, Workday, and Lever. (Dice MCP integration planned for automated sourcing and application).</p>
                                    </div>
                                </div>

                                <div className="engine-step">
                                    <div className="step-icon"><GitBranch size={20} /></div>
                                    <div className="step-content">
                                        <h4>Verified Proof of Work Mapping</h4>
                                        <p>Our Tiered LLM Router maps job requirements against verified university course descriptions, project documentation, and hackathon submissions to prevent hallucinated "matches".</p>
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
                            <div className="glass-panel" style={{ padding: '0', background: 'var(--bg-card)' }}>
                                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <BrainCircuit size={18} color="var(--accent-primary)" />
                                    <span style={{ fontWeight: '600' }}>Evaluation Engine</span>
                                </div>
                                <div style={{ padding: '24px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.95rem' }}>
                                        <span style={{ color: 'var(--text-secondary)' }}>Target Role:</span>
                                        <span style={{ fontWeight: '500' }}>Product Manager • TechCorp</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.95rem' }}>
                                        <span style={{ color: 'var(--text-secondary)' }}>Applicant Profile:</span>
                                        <span style={{ fontWeight: '500', fontFamily: 'monospace' }}>role_tpm.yaml</span>
                                    </div>

                                    <div style={{ height: '1px', background: 'var(--border-color)', margin: '8px 0' }}></div>

                                    <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '12px 16px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <Target size={18} color="var(--warning)" />
                                        <span style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>Gap Identified: <strong>Advanced Scrum</strong></span>
                                    </div>

                                    <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '16px', borderRadius: '8px' }}>
                                        <div style={{ color: 'var(--success)', fontWeight: '600', fontSize: '0.9rem', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Prescriptive Action:</div>
                                        <div style={{ fontSize: '0.95rem', lineHeight: '1.5' }}>Enroll in <strong>IE 5301</strong> (Spring Semester) to fill missing curriculum gap and increase interview probability by 18%.</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* AI Teaser Section */}
            <ArchitectureSection />

            {/* CTA Validation Section */}
            <section className="cta-section" style={{ paddingBottom: '60px' }}>
                <div className="container text-center animate-fade-up">
                    <div style={{ maxWidth: '600px', margin: '0 auto', background: 'linear-gradient(180deg, rgba(99, 102, 241, 0.1) 0%, var(--bg-secondary) 100%)', border: '1px solid rgba(99, 102, 241, 0.3)', padding: '48px 32px', borderRadius: '24px' }}>
                        <GraduationCap size={40} color="var(--accent-primary)" style={{ margin: '0 auto 24px auto' }} />
                        <h2 style={{ fontSize: '2rem', marginBottom: '16px' }}>Join the Alpha Cohort</h2>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>Stop guessing your applications. Get a pre-evaluated job feed tailored explicitly to your verified proof of work.</p>
                        <button className="btn-primary w-full" style={{ padding: '16px 0', fontSize: '1.1rem' }}>Request Beta Access</button>
                    </div>
                </div>
            </section>
            {/* [NEW] Gap Analysis Engine Section */}
            <section className="gap-analysis-section" style={{ padding: '100px 0', background: 'var(--bg-secondary)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient">Identify Your Hiring Gaps</h2>
                        <p className="subtitle">Stop applying blindly. See exactly where your current syllabus falls short of your dream role, and which project fixes it.</p>
                    </div>

                    <div className="engine-grid" style={{ alignItems: 'flex-start', marginTop: '60px' }}>
                        <div className="engine-text animate-fade-up">
                            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '24px', padding: '32px' }}>
                                <h3 style={{ marginBottom: '24px' }}>Select Target Role</h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                    {['Fullstack Engineer', 'Data Analyst', 'Product Manager'].map((role) => (
                                        <button
                                            key={role}
                                            className={`dept-btn ${role === 'Fullstack Engineer' ? 'active' : ''}`}
                                            style={{ width: '100%', textAlign: 'left', borderRadius: '12px', padding: '16px' }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span>{role}</span>
                                                <ArrowRight size={16} />
                                            </div>
                                        </button>
                                    ))}
                                </div>

                                <div className="mt-8">
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>SKILL COVERAGE MODEL</div>
                                    <div className="skill-tag">Next.js (Verified via CS 4301)</div>
                                    <div className="skill-tag">Postgres (Verified via Database Lab)</div>
                                    <div className="skill-tag-warning">Docker (GAP IDENTIFIED)</div>
                                </div>
                            </div>
                        </div>

                        <div className="engine-visual animate-fade-up delay-1">
                            <div className="glass-panel" style={{ padding: '40px', background: 'var(--bg-card)' }}>
                                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                                    <div style={{ fontSize: '3rem', fontWeight: '800', color: 'var(--accent-primary)' }}>84%</div>
                                    <div style={{ color: 'var(--text-secondary)', fontWeight: '600' }}>Overall Readiness Score</div>
                                </div>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                    <div className="audit-row">
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                            <span style={{ fontSize: '0.9rem' }}>Syllabus Alignment</span>
                                            <span style={{ color: 'var(--accent-primary)' }}>65%</span>
                                        </div>
                                        <div className="audit-progress"><div className="audit-bar" style={{ width: '65%' }}></div></div>
                                    </div>

                                    <div className="audit-row">
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                            <span style={{ fontSize: '0.9rem' }}>Project Evidence</span>
                                            <span style={{ color: 'var(--success)' }}>92%</span>
                                        </div>
                                        <div className="audit-progress"><div className="audit-bar" style={{ width: '92%', background: 'var(--success)' }}></div></div>
                                    </div>

                                    <div className="audit-row">
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                            <span style={{ fontSize: '0.9rem' }}>Hackathon/Extracurricular</span>
                                            <span style={{ color: 'var(--warning)' }}>40%</span>
                                        </div>
                                        <div className="audit-progress"><div className="audit-bar" style={{ width: '40%', background: 'var(--warning)' }}></div></div>
                                    </div>
                                </div>

                                <div style={{ marginTop: '40px', padding: '20px', background: 'rgba(255,165,0,0.05)', borderRadius: '12px', border: '1px solid rgba(255,165,0,0.2)' }}>
                                    <div style={{ color: 'var(--warning)', fontWeight: '700', fontSize: '0.85rem', marginBottom: '8px' }}>BRIDGE THE GAP:</div>
                                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>You are missing <strong>Containerization</strong>. Our AI suggests completing <strong>Lab 4: Dockerize</strong> or uploading your <strong>WebDev Project</strong> GitHub repo to hit 95%.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <FAQ
                title="Student FAQ"
                items={[
                    { question: "How does JobsProof keep my data safe?", answer: "We use jobsproof.com's institutional-grade infrastructure, including HSTS and DNSSEC protocols, to ensure your connection is never intercepted. All course material is encrypted via AES-256, and we only extract skill signatures—never selling your PII to third parties." },
                    { question: "Is this just another job board like LinkedIn?", answer: "No. LinkedIn shows you every job. We show you the 3-5 jobs where your exact course projects and elective choices fulfill 90%+ of the technical requirements, bypassing 'Years of Experience' filters." },
                    { question: "Does JobsProof cost money for students?", answer: "JobsProof is currently free for all active students within the UT System and select partner programs during our 2026 Beta phase." },
                    { question: "What if my syllabus is a PDF or image?", answer: "Our engine handles PDF, Docx, and even mobile photos of handouts. We use vision-models to parse the learning objectives and map them to industry-standard skill taxonomies." }
                ]}
            />
        </>
    );
}
