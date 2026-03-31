import { useState, useEffect } from 'react';
import { BrainCircuit, Briefcase, ArrowRight, CheckCircle2, FileText, Target, Map, Database, GitBranch, Github, ShieldCheck, Code } from 'lucide-react';
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
                            <span style={{ whiteSpace: 'nowrap' }}>Automated Career</span><br />
                            <span className="text-gradient" style={{ whiteSpace: 'nowrap' }}>Orchestration.</span>
                        </h1>

                        <div className="problem-statement" style={{ background: 'rgba(245, 158, 11, 0.05)', borderLeft: '3px solid var(--warning)', padding: '12px 16px', borderRadius: '0 8px 8px 0', marginBottom: '20px' }}>
                            <strong style={{ color: 'var(--warning)', display: 'block', marginBottom: '4px', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>The Problem</strong>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.4' }}>Stringing together 6 fragmented tools (Canva, AI wrappers, LinkedIn) just to get auto-rejected because you didn't know the exact ATS constraints or Visa rules.</span>
                        </div>

                        <p>Stop playing the guessing game. <strong>Thara</strong> is an autonomous orchestration agent that handles format traps, gap paralyzation, and ATS triage continuously.</p>

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

            {/* The Anti-Fabrication Feature Grid */}
            <section className="features-section">
                <div className="container">
                    <div className="section-header animate-fade-up">
                        <h2 className="text-gradient">The Anti-Fabrication Engine</h2>
                        <p>Most AI wrappers hallucinate fake metrics to pass ATS, destroying your reputation. We enforce absolute truth.</p>
                    </div>

                    <div className="feature-grid">
                        <div className="feature-card animate-fade-up delay-1">
                            <div className="feature-icon">
                                <ShieldCheck size={24} />
                            </div>
                            <h3>1. Zero Hallucinations</h3>
                            <p>We refuse to lie. If a job requires "AWS Lambda" and you don't have it, we don't invent a fake project. Your output remains 100% verifiable.</p>
                        </div>

                        <div className="feature-card animate-fade-up delay-2">
                            <div className="feature-icon">
                                <Map size={24} />
                            </div>
                            <h3>2. Actionable Gap Resolution</h3>
                            <p>Instead of lying, the AI identifies the missing skills, provides a customized project tutorial roadmap, and dynamically re-injects the new Github repo into your Context Profile once complete.</p>
                        </div>

                        <div className="feature-card animate-fade-up delay-3">
                            <div className="feature-icon">
                                <FileText size={24} />
                            </div>
                            <h3>3. The ATS Myth Buster</h3>
                            <p>Robots don't reject you because of "ugly formatting". They reject you because of missing technical signatures and hard Visa Knockout questions. We optimize for the machine-readable JSON layer first before outputting PDF.</p>
                        </div>

                        <div className="feature-card animate-fade-up delay-4">
                            <div className="feature-icon">
                                <CheckCircle2 size={24} />
                            </div>
                            <h3>4. Hard H-1B/F-1 Guardrails</h3>
                            <p>We actively scrape and read the security clearance and sponsorship parameters of every URL you paste. If they don't sponsor, we explicitly flag it, stopping the wasted effort immediately.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW Phase 3] Trajectory & Upskilling Strategy */}
            <section className="trajectory-section" style={{ padding: '100px 0', background: 'var(--bg-secondary)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient">Professional Trajectory Mapping</h2>
                        <p className="subtitle" style={{ maxWidth: '800px', margin: '0 auto' }}>
                            We don't just match keywords; we map your entire career trajectory. Thara identifies exactly how your university projects bridge the gap to your dream role.
                        </p>
                    </div>

                    <div className="engine-grid" style={{ marginTop: '60px', alignItems: 'center' }}>
                        {/* The Radar Chart Mockup */}
                        <div className="animate-fade-up delay-1" style={{ position: 'relative', width: '100%', maxWidth: '450px', margin: '0 auto' }}>
                            <div style={{ paddingBottom: '100%', position: 'relative', background: 'radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%)', borderRadius: '50%', border: '1px dashed var(--border-color)' }}>
                                {/* SVG Radar */}
                                <svg viewBox="0 0 100 100" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', transform: 'rotate(-18deg)' }}>
                                    {/* Grid Lines */}
                                    <circle cx="50" cy="50" r="10" fill="none" stroke="var(--border-color)" strokeWidth="0.5" />
                                    <circle cx="50" cy="50" r="20" fill="none" stroke="var(--border-color)" strokeWidth="0.5" />
                                    <circle cx="50" cy="50" r="30" fill="none" stroke="var(--border-color)" strokeWidth="0.5" />
                                    <circle cx="50" cy="50" r="40" fill="none" stroke="var(--border-color)" strokeWidth="0.5" />
                                    
                                    {/* Axis */}
                                    {[0, 72, 144, 216, 288].map(angle => (
                                        <line key={angle} x1="50" y1="50" x2={50 + 40 * Math.cos(angle * Math.PI / 180)} y2={50 + 40 * Math.sin(angle * Math.PI / 180)} stroke="var(--border-color)" strokeWidth="0.5" strokeDasharray="2 2" />
                                    ))}

                                    {/* Data Polygon - Current Profile */}
                                    <polygon points="50,25 75,40 65,70 35,70 25,40" fill="rgba(99, 102, 241, 0.2)" stroke="var(--accent-primary)" strokeWidth="1" />
                                    
                                    {/* Target Node Markings */}
                                    <circle cx="50" cy="15" r="2" fill="var(--success)" />
                                    <text x="52" y="12" fontSize="3" fill="var(--text-secondary)" fontWeight="600">Architectural Depth</text>
                                    
                                    <circle cx="85" cy="45" r="2" fill="var(--success)" />
                                    <text x="88" y="47" fontSize="3" fill="var(--text-secondary)" fontWeight="600">Product Strategy</text>

                                    <circle cx="70" cy="85" r="2" fill="var(--warning)" />
                                    <text x="73" y="88" fontSize="3" fill="var(--warning)" fontWeight="600">Missing: Stakeholder Exp</text>
                                </svg>
                            </div>
                        </div>

                        {/* Upskilling Project Card */}
                        <div className="animate-fade-up delay-2">
                            <div className="b2b-card" style={{ borderLeft: '4px solid var(--warning)', background: 'var(--bg-card)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                                    <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '10px', borderRadius: '10px' }}>
                                        <GitBranch color="var(--warning)" size={24} />
                                    </div>
                                    <div>
                                        <h4 style={{ margin: 0 }}>Strategic Gap Detected</h4>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--warning)', fontWeight: '600' }}>GOAL: TECHNICAL PRODUCT MANAGER</div>
                                    </div>
                                </div>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '24px' }}>
                                    You have 92% technical match, but zero evidence of "Roadmap Prioritization." Most AI would lie. <strong>Thara generates a project spec instead.</strong>
                                </p>
                                
                                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)', marginBottom: '20px' }}>
                                    <div style={{ fontSize: '0.85rem', fontWeight: '700', marginBottom: '8px', color: 'var(--accent-primary)' }}>RECOMMENDED ROADMAP:</div>
                                    <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>"Build a Prioritized Feature Backlog using RICE scoring for your Payment Gateway Repo."</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '8px' }}>Estimated Effort: 4 Hours • Value: High Stakeholder Signal</div>
                                </div>

                                <button className="btn-secondary" style={{ width: '100%', fontSize: '0.9rem' }}>Deploy Roadmap to GitHub</button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Digital Twin / Master Context Section */}
            <section className="digital-twin-section" style={{ padding: '80px 0', background: 'var(--bg-primary)' }}>
                <div className="container">
                    <div className="engine-grid" style={{ alignItems: 'center', gap: '60px' }}>
                        <div className="animate-fade-up">
                            <h2 className="text-gradient">Your Professional Digital Twin</h2>
                            <p className="subtitle">
                                Thara maintains a perpetually updated "Master Context" of your professional life inside a hybrid SQL/Vector memory bank. You never fill out a form again.
                            </p>
                            
                            <ul style={{ listStyle: 'none', padding: 0, marginTop: '32px' }}>
                                <li style={{ marginBottom: '20px', display: 'flex', gap: '16px' }}>
                                    <div style={{ minWidth: '40px', height: '40px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <Database size={20} color="var(--accent-primary)" />
                                    </div>
                                    <div>
                                        <h4 style={{ margin: '0 0 4px 0' }}>Semantic Memory</h4>
                                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Every lab repo, performance review, and side-project is vector-indexed for instant retrieval.</p>
                                    </div>
                                </li>
                                <li style={{ display: 'flex', gap: '16px' }}>
                                    <div style={{ minWidth: '40px', height: '40px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <Code size={20} color="var(--success)" />
                                    </div>
                                    <div>
                                        <h4 style={{ margin: '0 0 4px 0' }}>LaTeX Native Export</h4>
                                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>One source of truth, infinite structural variations (TPM, SDE, Product) compiled in seconds.</p>
                                    </div>
                                </li>
                            </ul>
                        </div>

                        <div className="animate-fade-up delay-1">
                            <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 30px 60px rgba(0,0,0,0.4)', fontFamily: 'monospace' }}>
                                <div style={{ background: '#161b22', padding: '12px 20px', borderBottom: '1px solid #30363d', fontSize: '0.8rem', color: '#8b949e', display: 'flex', justifyContent: 'space-between' }}>
                                    <span>master_profile.yaml</span>
                                    <span>UTF-8</span>
                                </div>
                                <div style={{ padding: '24px', fontSize: '0.85rem', lineHeight: '1.6', color: '#c9d1d9' }}>
                                    <div><span style={{ color: '#ff7b72' }}>User_Profile</span>:</div>
                                    <div style={{ paddingLeft: '16px' }}><span style={{ color: '#79c0ff' }}>Clerk_ID</span>: <span style={{ color: '#a5d6ff' }}>"user_123xyz"</span></div>
                                    <div style={{ paddingLeft: '16px' }}><span style={{ color: '#ff7b72' }}>Experience</span>:</div>
                                    <div style={{ paddingLeft: '32px' }}>- <span style={{ color: '#79c0ff' }}>Company</span>: <span style={{ color: '#a5d6ff' }}>"Google"</span></div>
                                    <div style={{ paddingLeft: '32px' }}><span style={{ color: '#79c0ff' }}>Role</span>: <span style={{ color: '#a5d6ff' }}>"Technical Product Manager"</span></div>
                                    <div style={{ paddingLeft: '32px' }}><span style={{ color: '#79c0ff' }}>Raw_Context_Dump</span>: <span style={{ color: '#7ee787' }}>"Launched API gateway... 1M requests/day..."</span></div>
                                    <div style={{ paddingLeft: '16px' }}><span style={{ color: '#ff7b72' }}>Skills_Inventory</span>:</div>
                                    <div style={{ paddingLeft: '32px' }}><span style={{ color: '#79c0ff' }}>Hard_Skills</span>: [<span style={{ color: '#a5d6ff' }}>"Python"</span>, <span style={{ color: '#a5d6ff' }}>"Kafka"</span>, <span style={{ color: '#a5d6ff' }}>"SQL"</span>]</div>
                                    <div style={{ paddingLeft: '16px' }}><span style={{ color: '#ff7b72' }}>Upskilling_Roadmap</span>:</div>
                                    <div style={{ paddingLeft: '32px' }}>- <span style={{ color: '#79c0ff' }}>Skill</span>: <span style={{ color: '#a5d6ff' }}>"Backlog Prioritization"</span></div>
                                    <div style={{ paddingLeft: '32px' }}><span style={{ color: '#79c0ff' }}>Status</span>: <span style={{ color: '#f2cc60' }}>"In Progress"</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW] The Emotional ROI Banner */}
            <section className="roi-banner" style={{ padding: '60px 0', background: 'linear-gradient(90deg, var(--bg-card), rgba(99, 102, 241, 0.05))', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
                <div className="container text-center animate-fade-up">
                    <h2 style={{ fontSize: '2.5rem', marginBottom: '16px' }}>Get <span className="text-gradient">15 Hours</span> of Your Week Back</h2>
                    <p style={{ maxWidth: '700px', margin: '0 auto', fontSize: '1.1rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                        The constant cycle of tailoring resumes on Canva and fighting with isolated Workday portals is emotionally exhausting. Thara eliminates the logistical dread of the job hunt so you can focus your mental energy on mastering your coursework and crushing the actual technical interviews.
                    </p>
                </div>
            </section>

            {/* The 6-Step Journey Solution */}
            <section className="competitive-section">
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2>Solving the 6-Step Friction Loop</h2>
                        <p className="subtitle" style={{ maxWidth: '700px', margin: '0 auto' }}>You are forced to string together multiple fragmented tools just to get an interview. We combined every phase into one unified agentic ecosystem.</p>
                    </div>

                    <div className="phase-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
                        {/* Friction 1: The Format Trap */}
                        <div className="phase-card animate-fade-up delay-1">
                            <div className="phase-header">
                                <span className="phase-number">1</span>
                                <h3>The Format Trap</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Wasting 5 hours nudging margins in Word or Canva, only to have Workday mangle the PDF.</div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">Thara Solution</div>
                                    <div className="way-content">We ingest your Master Context and dynamically compile a pristine, ATS-parseable LaTeX PDF in seconds.</div>
                                </div>
                            </div>
                        </div>

                        {/* Friction 2: Tool Fragmentation */}
                        <div className="phase-card animate-fade-up delay-2">
                            <div className="phase-header">
                                <span className="phase-number">2</span>
                                <h3>Tool Fragmentation</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Using Huntr for tracking, ChatGPT for writing, and LinkedIn for searching—none of which integrate naturally.</div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">Thara Solution</div>
                                    <div className="way-content">A single agentic supervisor manages your entire pipeline seamlessly without context loss.</div>
                                </div>
                            </div>
                        </div>

                        {/* Friction 3: Gap Paralysis */}
                        <div className="phase-card animate-fade-up delay-3">
                            <div className="phase-header">
                                <span className="phase-number">3</span>
                                <h3>Gap Paralysis</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Seeing a hard requirement for "Kafka", realizing you don't confidently know it, and abandoning the application.</div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">Thara Solution</div>
                                    <div className="way-content">The AI builds a bespoke weekend project spec to bridge the exact technical gap holding you back from Senior roles.</div>
                                </div>
                            </div>
                        </div>

                        {/* Friction 4: Sourcing & Sponsorship */}
                        <div className="phase-card animate-fade-up delay-4">
                            <div className="phase-header">
                                <span className="phase-number">4</span>
                                <h3>Sourcing & Sponsorship</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Scrolling LinkedIn for hours, guessing if a company ultimately sponsors F-1 OPT or H-1B visas.</div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">Thara Solution</div>
                                    <div className="way-content">Background agents proactively scrape "ghost jobs", and explicitly verify sponsorship clauses prior to alerting you.</div>
                                </div>
                            </div>
                        </div>

                        {/* Friction 5: ATS Triage */}
                        <div className="phase-card animate-fade-up delay-5">
                            <div className="phase-header">
                                <span className="phase-number">5</span>
                                <h3>ATS Triage</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Blindly submitting a PDF and hoping your generic bullet points satisfy the underlying backend parsing engine.</div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">Thara Solution</div>
                                    <div className="way-content">We enforce absolute Truth and output verified technical signatures to pass the exact ATS algorithms mathematically.</div>
                                </div>
                            </div>
                        </div>

                        {/* Friction 6: The Final Mile */}
                        <div className="phase-card animate-fade-up delay-6">
                            <div className="phase-header">
                                <span className="phase-number">6</span>
                                <h3>The Final Mile</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Securing the recruiter screen but freezing up on heavily weighted Behavioral/STAR-method questions.</div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">Thara Solution</div>
                                    <div className="way-content">The AI analyzes the parsed JD and generates an automated interview narrative cheat-sheet mapping to your Master Context.</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* The Conviction Score Showcase */}
            <section className="score-showcase-section" style={{ padding: '80px 0', background: 'var(--bg-card)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient">The "Apply Conviction" Score</h2>
                        <p className="subtitle" style={{ maxWidth: '700px', margin: '0 auto' }}>Before you generate a resume, Thara's evaluator reads the JD, compares it against your complete history, and gives you the objective, mathematical probability of passing the human screen.</p>
                    </div>

                    <div style={{ maxWidth: '900px', margin: '40px auto 0 auto', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }} className="animate-fade-up delay-1">
                        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.1)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <Target size={20} color="var(--accent-primary)" />
                                <span style={{ fontWeight: '600', fontSize: '1.1rem' }}>Pre-Flight Evaluation: Technical Product Manager</span>
                            </div>
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>Engine: adk_orchestrator.py</span>
                        </div>
                        
                        <div style={{ padding: '32px 24px', display: 'grid', gridTemplateColumns: 'minmax(250px, 1fr) 2fr', gap: '32px' }}>
                            {/* The Score */}
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '12px', padding: '32px' }}>
                                <div style={{ fontSize: '4.5rem', fontWeight: '800', lineHeight: '1', color: 'var(--success)', marginBottom: '8px' }}>87<span style={{ fontSize: '2rem' }}>%</span></div>
                                <div style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: '600', color: 'var(--text-secondary)' }}>Conviction Score</div>
                                <div style={{ marginTop: '16px', padding: '6px 12px', background: 'rgba(16,185,129,0.1)', color: 'var(--success)', borderRadius: '20px', fontSize: '0.8rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <CheckCircle2 size={14} /> HIGH ROI TARGET
                                </div>
                            </div>

                            {/* The Breakdown */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', fontWeight: '500' }}>
                                        <span>Hard Skills / Tech Stack Match</span>
                                        <span style={{ color: 'var(--success)' }}>92%</span>
                                    </div>
                                    <div style={{ width: '100%', height: '6px', background: 'var(--bg-card)', borderRadius: '3px', overflow: 'hidden' }}>
                                        <div style={{ width: '92%', height: '100%', background: 'var(--success)' }}></div>
                                    </div>
                                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '6px' }}>Verified AWS, Python, and Kafka projects in your profile.</p>
                                </div>

                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', fontWeight: '500' }}>
                                        <span>Years of Experience Weighting</span>
                                        <span style={{ color: 'var(--warning)' }}>75%</span>
                                    </div>
                                    <div style={{ width: '100%', height: '6px', background: 'var(--bg-card)', borderRadius: '3px', overflow: 'hidden' }}>
                                        <div style={{ width: '75%', height: '100%', background: 'var(--warning)' }}></div>
                                    </div>
                                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '6px' }}>JD asks for 4 years; you have 2.5. Overriding with heavy impact metrics.</p>
                                </div>

                                <div style={{ background: 'rgba(239, 68, 68, 0.05)', borderLeft: '3px solid var(--error)', padding: '12px 16px', borderRadius: '0 8px 8px 0', marginTop: '8px' }}>
                                    <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', color: 'var(--error)', marginBottom: '4px' }}>Critical Guardrail Check</span>
                                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>F-1 OPT/H-1B Visa sponsorship explicitly advertised. Safe to apply.</span>
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
                        <p className="subtitle" style={{ maxWidth: '900px', margin: '0 auto', lineHeight: '1.6' }}>
                            Stop cold-DMing strangers on LinkedIn who will never answer you. JobsProof analyzes historical placement data from your specific university program to build a deterministic graph of warm leads. We show you exactly where your program's alumni were hired, what their starting titles were, and the exact "Verified Match" curriculum traits that got them their offer.
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

            {/* CTA Validation Section -> Replaced with Open Source CTA */}
            <section className="cta-section" style={{ paddingBottom: '60px' }}>
                <div className="container text-center animate-fade-up">
                    <div style={{ maxWidth: '800px', margin: '0 auto', background: 'linear-gradient(180deg, rgba(99, 102, 241, 0.1) 0%, var(--bg-secondary) 100%)', border: '1px solid rgba(99, 102, 241, 0.3)', padding: '48px 32px', borderRadius: '24px' }}>
                        <Github size={48} color="var(--accent-primary)" style={{ margin: '0 auto 24px auto' }} />
                        <h2 style={{ fontSize: '2rem', marginBottom: '16px' }}>Want to Contribute?</h2>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', fontSize: '1.05rem', lineHeight: '1.6' }}>JobsProof is powered by open-source agentic pipelines. We are actively building out multi-platform ATS execution, advanced LaTeX compilation engines, and deeper intelligence matrices. Join us in breaking the resume black box.</p>
                        <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
                            <a href="https://github.com/nagarajaabhishek/jobs" target="_blank" rel="noopener noreferrer" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}>
                                <GitBranch size={18} /> Contribute to Job Automation
                            </a>
                            <a href="https://github.com/nagarajaabhishek/resume_agent" target="_blank" rel="noopener noreferrer" className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}>
                                <GitBranch size={18} /> Contribute to Resume Agent
                            </a>
                        </div>
                    </div>
                </div>
            </section>
            {/* Student Pricing Section */}
            <section className="pricing-section" style={{ padding: '80px 0' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2>Pricing for Students</h2>
                        <p className="subtitle">Stop paying subscriptions to 5 different fragmented products.</p>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '32px', justifyContent: 'center', marginTop: '40px' }}>
                        {/* Free Tier */}
                        <div className="pricing-card animate-fade-up delay-1" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '40px', width: '100%', maxWidth: '400px', display: 'flex', flexDirection: 'column' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '16px' }}>Base Console</div>
                            <div style={{ fontSize: '3rem', fontWeight: '800', lineHeight: '1', marginBottom: '8px' }}>$0<span style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: '400' }}> / forever</span></div>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '32px' }}>Perfect for manual targeting.</p>
                            
                            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 40px 0', display: 'flex', flexDirection: 'column', gap: '16px', flexGrow: 1 }}>
                                <li style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.95rem' }}><CheckCircle2 size={18} color="var(--success)" /> Manual JD Parsing</li>
                                <li style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.95rem' }}><CheckCircle2 size={18} color="var(--success)" /> LaTeX Resume Compilation</li>
                                <li style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.95rem' }}><CheckCircle2 size={18} color="var(--success)" /> Basic Gap Analysis</li>
                            </ul>
                            <button className="btn-secondary" style={{ width: '100%' }}>Launch Engine</button>
                        </div>

                        {/* Pro Tier */}
                        <div className="pricing-card animate-fade-up delay-2" style={{ background: 'linear-gradient(180deg, rgba(99, 102, 241, 0.05) 0%, rgba(99, 102, 241, 0) 100%)', border: '1px solid var(--accent-primary)', borderRadius: '16px', padding: '40px', width: '100%', maxWidth: '400px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
                            <div style={{ position: 'absolute', top: 0, left: '50%', transform: 'translate(-50%, -50%)', background: 'var(--accent-primary)', color: 'white', padding: '4px 16px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '1px' }}>Automated Pilot</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--accent-primary)', marginBottom: '16px' }}>Thara Orchestrator</div>
                            <div style={{ fontSize: '3rem', fontWeight: '800', lineHeight: '1', marginBottom: '8px' }}>$19<span style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: '400' }}> / month</span></div>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '32px' }}>Full-scale background automation.</p>
                            
                            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 40px 0', display: 'flex', flexDirection: 'column', gap: '16px', flexGrow: 1 }}>
                                <li style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.95rem' }}><CheckCircle2 size={18} color="var(--accent-primary)" /> Automated Background Sourcing</li>
                                <li style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.95rem' }}><CheckCircle2 size={18} color="var(--accent-primary)" /> Apply Conviction Scoring Loop</li>
                                <li style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.95rem' }}><CheckCircle2 size={18} color="var(--accent-primary)" /> Anti-Fabrication Agent Execution</li>
                                <li style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.95rem' }}><CheckCircle2 size={18} color="var(--accent-primary)" /> Cover Letter & Outreach Generation</li>
                            </ul>
                            <button className="btn-primary" style={{ width: '100%' }}>Automate My Job Search</button>
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
