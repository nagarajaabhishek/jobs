import { useState } from 'react';
import { BrainCircuit, Briefcase, Network, ArrowRight, CheckCircle2, FileText, Target, Map, Database, GitBranch, GraduationCap } from 'lucide-react';
import CompetitiveTable from '../components/CompetitiveTable';
import FAQ from '../components/FAQ';

export default function StudentLanding() {
    const [activeResume, setActiveResume] = useState('ba');

    return (
        <>
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
                        <p>The only job feed that instantly tells you if you're a fit based on your syllabus, projects, and hackathons. <strong>JobsProof.com</strong> validates your background so you only apply to high-match roles. Zero text copying required.</p>

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

            {/* Phase-Based Competitive Analysis */}
            <section className="competitive-section">
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2>The Broken Recruitment Pipeline</h2>
                        <p className="subtitle" style={{ maxWidth: '700px', margin: '0 auto' }}>Students are forced to string together multiple fragmented tools just to get an interview. We combined every phase into one seamless platform.</p>
                    </div>

                    <div className="phase-grid">
                        {/* Phase 1: Sourcing */}
                        <div className="phase-card animate-fade-up delay-1">
                            <div className="phase-header">
                                <span className="phase-number">1</span>
                                <h3>Sourcing Roles</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Endless scrolling through noisy feeds, guessing if a company hires from your major.</div>
                                    <div className="tool-tags">
                                        <span className="tool-tag">LinkedIn</span>
                                        <span className="tool-tag">Indeed</span>
                                        <span className="tool-tag">Handshake</span>
                                    </div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">JobsProof.com</div>
                                    <div className="way-content">A curated daily feed of the top 100 roles specifically targeting your university.</div>
                                </div>
                            </div>
                        </div>

                        {/* Phase 2: Evaluation */}
                        <div className="phase-card animate-fade-up delay-2">
                            <div className="phase-header">
                                <span className="phase-number">2</span>
                                <h3>Evaluating Fit</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Blindly applying to roles and hoping your generic resume passes the ATS parser.</div>
                                    <div className="tool-tags">
                                        <span className="tool-tag">Manual Review</span>
                                        <span className="tool-tag">Guesswork</span>
                                    </div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">JobsProof.com</div>
                                    <div className="way-content">Instant % match against all your ATS-optimized profiles based on verified syllabi, hackathons, and GitHub projects.</div>
                                </div>
                            </div>
                        </div>

                        {/* Phase 3: Tailoring */}
                        <div className="phase-card animate-fade-up delay-3">
                            <div className="phase-header">
                                <span className="phase-number">3</span>
                                <h3>Tailoring Resumes</h3>
                            </div>
                            <div className="phase-body">
                                <div className="status-quo">
                                    <div className="way-label">The Old Way</div>
                                    <div className="way-content">Spending hours tweaking keywords and asking AI to rewrite bullets for every app.</div>
                                    <div className="tool-tags">
                                        <span className="tool-tag">ChatGPT</span>
                                        <span className="tool-tag">Teal</span>
                                        <span className="tool-tag">Word</span>
                                    </div>
                                </div>
                                <div className="our-way">
                                    <div className="way-label">JobsProof</div>
                                    <div className="way-content">One-click deployment using the highest-scoring pre-existing resume profile.</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Feature-Based Competitive Analysis */}
            <CompetitiveTable
                title="Why We Win"
                subtitle="We aren't just another job board. We are a targeted deployment system."
                competitorName="Standard Job Boards"
                rows={[
                    { feature: 'Matching Logic', us: 'Verified Proof of Work (Syllabus, Projects, Hackathons)', them: 'Keyword Spamming' },
                    { feature: 'Experience Credit', us: 'Syllabus-as-Experience (Bypass 3yr req)', them: 'Arbitrary "Years of Exp"' },
                    { feature: 'Transparency', us: 'Verified Visa & Direct ATS Timestamps', them: 'Ghost Jobs & Blind Filters' }
                ]}
            />

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
                                        <h4>Direct ATS Ingestion</h4>
                                        <p>We bypass LinkedIn "ghost jobs" by directly scraping validated openings from Greenhouse, Workday, and Lever.</p>
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
