import { useState, useEffect } from 'react';
import { ArrowRight, XCircle, ShieldCheck, Briefcase } from 'lucide-react';
import CompetitiveTable from '../components/CompetitiveTable';
import FAQ from '../components/FAQ';

export default function UniversityLanding() {
    useEffect(() => {
        document.title = "For Universities | JobsProof.com";
    }, []);

    const [activeDept, setActiveDept] = useState('engineering');

    const deptData = {
        engineering: {
            heatmap: [
                { label: 'Cloud Infrastructure (AWS/Azure)', levels: [4, 4, 5, 5], demand: ['98%', '99%', '102%', '105%'] },
                { label: 'Agile/Scrum Leadership', levels: [3, 4, 4, 5], demand: ['72%', '88%', '91%', '96%'] },
                { label: 'Legacy Waterfall Management', levels: [2, 1, 1, 0], demand: ['45%', '32%', '18%', '12%'], warning: true }
            ],
            evidence: [
                { req: '1.2 Program Educational Objectives', source: 'CS 4301 - Senior Capstone', data: 'Verified mastery of "Real-world Project Life Cycles" for 142 students.' },
                { req: '3.5 Professional Ethics', source: 'IE 5301 - Case Study Submissions', data: 'Ethical framework application verified via 28 peer-reviewed hackathon repos.' }
            ],
            insight: { course: 'IE 5302', focus: 'Agile Scrum', surge: '24%' }
        },
        business: {
            heatmap: [
                { label: 'Data-Driven Decision Making', levels: [4, 5, 5, 5], demand: ['92%', '102%', '108%', '112%'] },
                { label: 'FinTech Strategy', levels: [2, 3, 4, 5], demand: ['40%', '65%', '88%', '98%'] },
                { label: 'Standard Retail Management', levels: [3, 2, 2, 1], demand: ['60%', '45%', '40%', '25%'], warning: true }
            ],
            evidence: [
                { req: 'A.1 Strategic Orientation', source: 'MGMT 6301 - Market Analysis', data: '94% of students demonstrated "Competitive Moat Identification" in verified projects.' },
                { req: 'C.2 Numerical Competence', source: 'FIN 6301 - Excel Modeling', data: 'Verified student submissions confirm mastery of "Monte Carlo Simulations" for accreditation.' }
            ],
            insight: { course: 'MGMT 6305', focus: 'FinTech Analytics', surge: '38%' }
        },
        science: {
            heatmap: [
                { label: 'Bio-Informatics Pipelines', levels: [3, 4, 5, 5], demand: ['70%', '85%', '95%', '102%'] },
                { label: 'Computational Physics', levels: [2, 2, 3, 4], demand: ['35%', '45%', '60%', '82%'] },
                { label: 'Manual Data Entry/Tabulation', levels: [2, 1, 0, 0], demand: ['30%', '15%', '5%', '2%'], warning: true }
            ],
            evidence: [
                { req: 'LS-1 Biological Mechanisms', source: 'BIO 4301 - Lab Repos', data: 'Sequence alignment proficiency verified via automated analysis of 65 student GitHub repos.' },
                { req: 'LS-4 Lab Safety Compliance', source: 'CHEM 3301 - Digital Logs', data: 'Compliance mastery verified via timestamped digital project logs across 12 departments.' }
            ],
            insight: { course: 'BIO 4305', focus: 'Python for Bio-Science', surge: '42%' }
        }
    };

    const currentData = deptData[activeDept as keyof typeof deptData];

    return (
        <>
            <section className="hero-section" style={{ minHeight: '80vh', paddingTop: '20px', background: 'radial-gradient(ellipse at top, rgba(16, 185, 129, 0.1) 0%, var(--bg-primary) 70%)' }}>
                <div className="container text-center">
                    <div className="hero-content animate-fade-up" style={{ margin: '0 auto', maxWidth: '800px' }}>
                        <div className="b2b-badge" style={{ display: 'inline-block', margin: '0 auto 24px auto' }}>For Universities & Dept Heads</div>
                        <h1 style={{ fontSize: '3.5rem', lineHeight: '1.2', marginBottom: '24px', textAlign: 'center' }}>Eliminate the 1,889-to-1 <span style={{ color: 'var(--success)' }}>Counselor Bottleneck.</span></h1>
                        <p style={{ textAlign: 'center', margin: '0 auto 32px auto' }}>Your career center is overwhelmed. Thara acts as an autonomous Tier-1 AI Counselor for every student, freeing your staff to build high-leverage employer pipelines.</p>

                        <div className="cta-group" style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
                            <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--success)', color: '#000' }}>
                                Request Department Demo <ArrowRight size={18} />
                            </button>
                            <button className="btn-secondary">View Sample Analytics</button>
                        </div>
                    </div>
                </div>
            </section>

            {/* The 1889:1 Bottleneck Section */}
            <section className="bottleneck-section" style={{ padding: '80px 0', background: 'var(--bg-secondary)' }}>
                <div className="container text-center">
                    <div className="section-header animate-fade-up">
                        <h2 style={{ color: 'var(--warning)', fontSize: '3rem', marginBottom: '8px' }}>1,889 to 1</h2>
                        <h3 className="text-secondary" style={{ fontSize: '1.5rem', fontWeight: '500' }}>The Median Student-to-Career-Counselor Ratio</h3>
                    </div>
                    
                    <p className="subtitle animate-fade-up delay-1" style={{ maxWidth: '800px', margin: '24px auto', lineHeight: '1.6' }}>
                        It is physically impossible for traditional university career centers to review thousands of custom resumes, conduct technical mock interviews, and generate personalized "missing skill" roadmaps for every student. 
                    </p>

                    <div className="bottleneck-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginTop: '48px' }}>
                        <div className="b2b-card" style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                            <h4 style={{ color: 'var(--text-primary)', marginBottom: '12px' }}>The Result</h4>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Overwhelmed counselors resort to handing out generic, 15-year-old PDF templates. Students resort to spamming ChatGPT, resulting in auto-rejections and tanking the university's post-graduation employment KPIs.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* The Tier-1 Setup Section */}
            <section className="tier-setup-section" style={{ padding: '100px 0', background: 'var(--bg-primary)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient-green">Deploy a Tier-1 AI Career Counselor</h2>
                        <p className="subtitle" style={{ maxWidth: '800px', margin: '0 auto' }}>
                            Thara operates 24/7 to output perfect entry-level documents for all 1,889 students simultaneously, allowing your human experts to do what they do best: build relationships.
                        </p>
                    </div>

                    <div className="engine-grid" style={{ marginTop: '60px' }}>
                        {/* The AI Responsibility */}
                        <div className="b2b-card animate-fade-up delay-1" style={{ borderTop: '4px solid var(--accent-primary)' }}>
                            <h3>Tier-1: Thara Agent Ecosystem</h3>
                            <div style={{ color: 'var(--text-secondary)', marginBottom: '20px', fontStyle: 'italic' }}>Infinite Scale. Zero Burnout.</div>
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                <li style={{ marginBottom: '12px' }}>✔️ Ingests 4-years of course syllabi</li>
                                <li style={{ marginBottom: '12px' }}>✔️ Runs strict ATS validation scoring</li>
                                <li style={{ marginBottom: '12px' }}>✔️ Acts as a harsh "Hiring Bar" critic</li>
                                <li style={{ marginBottom: '12px' }}>✔️ Outputs pixel-perfect LaTeX PDFs</li>
                            </ul>
                        </div>

                        {/* The Human Responsibility */}
                        <div className="b2b-card animate-fade-up delay-2" style={{ borderTop: '4px solid var(--success)' }}>
                            <h3>Tier-2: Your Human Staff</h3>
                            <div style={{ color: 'var(--text-secondary)', marginBottom: '20px', fontStyle: 'italic' }}>High-Leverage Work Only.</div>
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                <li style={{ marginBottom: '12px' }}>🤝 Deep emotional counseling for students</li>
                                <li style={{ marginBottom: '12px' }}>🤝 Cultivating Alumni Network pipelines</li>
                                <li style={{ marginBottom: '12px' }}>🤝 Direct recruiter relationship building</li>
                                <li style={{ marginBottom: '12px' }}>🤝 Strategy and hiring partnership negotiations</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW] Market Demand Heatmap Mockup */}
            <section className="heatmap-section" style={{ padding: '80px 0', background: 'var(--bg-primary)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient-green">Market Demand vs. Curriculum Heatmap</h2>
                        <p className="subtitle" style={{ maxWidth: '800px', margin: '0 auto' }}>
                            Identify exactly where your department's electives are out of sync with regional hiring surges.
                        </p>
                    </div>

                    {/* Department Toggles */}
                    <div className="dept-toggles animate-fade-up">
                        <button className={`dept-btn ${activeDept === 'engineering' ? 'active' : ''}`} onClick={() => setActiveDept('engineering')}>Engineering</button>
                        <button className={`dept-btn ${activeDept === 'business' ? 'active' : ''}`} onClick={() => setActiveDept('business')}>B-School</button>
                        <button className={`dept-btn ${activeDept === 'science' ? 'active' : ''}`} onClick={() => setActiveDept('science')}>Science</button>
                    </div>

                    <div className="heatmap-container animate-fade-up delay-1">
                        <div className="heatmap-header">
                            <div className="heatmap-label">Skill Cluster</div>
                            <div className="heatmap-timeline">
                                <span>Q1 '26</span>
                                <span>Q2 '26</span>
                                <span>Q3 '26</span>
                                <span>Q4 '26</span>
                            </div>
                        </div>
                        {currentData.heatmap.map((row, idx) => (
                            <div key={idx} className={`heatmap-row ${row.warning ? 'warning' : ''}`}>
                                <div className="row-label">{row.label}</div>
                                <div className="heatmap-cells">
                                    {row.levels.map((level, lIdx) => (
                                        <div key={lIdx} className={`cell level-${level}`}>{row.demand[lIdx]} Demand</div>
                                    ))}
                                </div>
                            </div>
                        ))}
                        <div className="heatmap-footer">
                            <div className="insight-box">
                                <span className="text-success">● High ROI Opportunity:</span> Update <strong>{currentData.insight.course}</strong> to focus on <strong>{currentData.insight.focus}</strong> to capture {currentData.insight.surge} hiring surge.
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW Phase 4] Accreditation Evidence Vault */}
            <section className="accreditation-vault" style={{ padding: '100px 0', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)' }}>
                <div className="container">
                    <div className="engine-grid" style={{ alignItems: 'center', gap: '60px' }}>
                        <div className="animate-fade-up">
                            <div className="b2b-badge" style={{ marginBottom: '16px' }}>Audit Readiness</div>
                            <h2 className="text-gradient-green">The Accreditation Evidence Vault</h2>
                            <p className="subtitle">
                                Stop hunting for course artifacts months before your audit. Thara maps every student GitHub repo and lab submission directly to your ABET, AACSB, or SACSCOC learning objectives in real-time.
                            </p>
                            
                            <div style={{ marginTop: '32px' }}>
                                <div className="b2b-card" style={{ background: 'rgba(255,255,255,0.03)', marginBottom: '16px' }}>
                                    <div style={{ fontWeight: '700', color: 'var(--success)', marginBottom: '4px' }}>1-Click Audit Reports</div>
                                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Export comprehensive evidence dossiers for internal reviews or external accreditation boards.</p>
                                </div>
                                <div className="b2b-card" style={{ background: 'rgba(255,255,255,0.03)' }}>
                                    <div style={{ fontWeight: '700', color: 'var(--success)', marginBottom: '4px' }}>Zero Faculty Intervention</div>
                                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Data is ingested directly from the LMS, requiring no manual tagging or "upload weeks" from your professors.</p>
                                </div>
                            </div>
                        </div>

                        <div className="animate-fade-up delay-1">
                            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 40px rgba(0,0,0,0.3)' }}>
                                <div style={{ padding: '16px 20px', background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontWeight: '600', fontSize: '0.9rem' }}>Audit Mode: Accreditation Mapping</span>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--success)', fontWeight: '700' }}>● LIVE AUDIT DATA</span>
                                </div>
                                <div style={{ padding: '24px' }}>
                                    {[
                                        { obj: 'ABET 3.5: Ethics in Engineering', source: 'IE 5301 Submissions', count: '142 Files', status: 'VERIFIED' },
                                        { obj: 'AACSB A.1: Strategic Decisioning', source: 'MGMT 6301 Projects', count: '210 Repos', status: 'VERIFIED' },
                                        { obj: 'SACSCOC 8.2.a: Student Outcomes', source: 'All Department Labs', count: '1,200+ Artifacts', status: 'MAPPED' }
                                    ].map((item, idx) => (
                                        <div key={idx} style={{ padding: '16px', border: '1px solid var(--border-color)', borderRadius: '12px', marginBottom: '12px', background: 'rgba(0,0,0,0.1)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                                <span style={{ fontSize: '0.85rem', fontWeight: '700' }}>{item.obj}</span>
                                                <span style={{ fontSize: '0.7rem', color: 'var(--success)', fontWeight: '800' }}>{item.status}</span>
                                            </div>
                                            <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                <span>Source: {item.source}</span>
                                                <span>Evidence: {item.count}</span>
                                            </div>
                                        </div>
                                    ))}
                                    <button className="btn-primary" style={{ width: '100%', marginTop: '12px', fontSize: '0.85rem', background: '#333', color: '#fff', border: 'none' }}>Download Full Accreditation Dossier (.zip)</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW] The Status Quo vs. JobsProof */}
            <section className="xy-analysis-section" style={{ padding: '100px 0', background: 'var(--bg-primary)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient-green">Quality of Hire vs. The Status Quo</h2>
                        <p className="subtitle" style={{ maxWidth: '800px', margin: '0 auto' }}>
                            Employers are ignoring generic career portals. We rebuild their trust in your university by providing a unified, certified talent pipeline.
                        </p>
                    </div>

                    <div className="engine-grid" style={{ marginTop: '60px' }}>
                        {/* Status Quo */}
                        <div className="b2b-card animate-fade-up delay-1" style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                                <div style={{ background: 'var(--warning)', padding: '12px', borderRadius: '12px' }}>
                                    <XCircle color="#000" size={24} />
                                </div>
                                <h3 style={{ margin: 0, fontSize: '1.4rem' }}>The Status Quo</h3>
                            </div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px', fontStyle: 'italic' }}>Handshake, Symplicity, or generic job boards.</div>
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                <li style={{ marginBottom: '16px', display: 'flex', gap: '12px', color: 'var(--text-secondary)' }}>
                                    <span style={{ color: 'var(--warning)', fontWeight: 'bold' }}>✗</span>
                                    <span><strong>Low Trust:</strong> Employers suspect resumes are AI-hallucinated.</span>
                                </li>
                                <li style={{ marginBottom: '16px', display: 'flex', gap: '12px', color: 'var(--text-secondary)' }}>
                                    <span style={{ color: 'var(--warning)', fontWeight: 'bold' }}>✗</span>
                                    <span><strong>High Noise:</strong> Recruiters sift through 1,000s of keyword dumps.</span>
                                </li>
                                <li style={{ display: 'flex', gap: '12px', color: 'var(--text-secondary)' }}>
                                    <span style={{ color: 'var(--warning)', fontWeight: 'bold' }}>✗</span>
                                    <span><strong>No Context:</strong> "Python" could mean a 1-hour bootcamp or a 4-month graded thesis.</span>
                                </li>
                            </ul>
                        </div>

                        {/* JobsProof */}
                        <div className="b2b-card animate-fade-up delay-2" style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid var(--success)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                                <div style={{ background: 'var(--success)', padding: '12px', borderRadius: '12px' }}>
                                    <ShieldCheck color="#000" size={24} />
                                </div>
                                <h3 style={{ margin: 0, fontSize: '1.4rem', color: 'var(--success)' }}>The JobsProof Talent Pipeline</h3>
                            </div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px', fontStyle: 'italic' }}>Deterministic, curriculum-anchored hiring profiles.</div>
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                <li style={{ marginBottom: '16px', display: 'flex', gap: '12px', color: 'var(--text-secondary)' }}>
                                    <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>✓</span>
                                    <span><strong>High Trust:</strong> Core skills are deterministically proven against your syllabi.</span>
                                </li>
                                <li style={{ marginBottom: '16px', display: 'flex', gap: '12px', color: 'var(--text-secondary)' }}>
                                    <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>✓</span>
                                    <span><strong>Curated Quality:</strong> Employers see pre-ranked matches, not an unfiltered firehose.</span>
                                </li>
                                <li style={{ display: 'flex', gap: '12px', color: 'var(--text-secondary)' }}>
                                    <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>✓</span>
                                    <span><strong>Deep Context:</strong> "Python" is linked directly to passing grades on CS 4305 Lab Repos.</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW] The Employer Bridge Section */}
            <section className="employer-bridge-section" style={{ padding: '100px 0', background: 'var(--bg-secondary)' }}>
                <div className="container">
                    <div className="engine-grid" style={{ alignItems: 'center' }}>
                        <div className="engine-text animate-fade-up">
                            <h2 className="text-gradient">The Employer-Facing Feedback Loop</h2>
                            <p className="subtitle">Demonstrate real placement ROI to your board. We show you exactly how employers interact with your student talent pool.</p>
                            <div className="b2b-card mt-6" style={{ background: 'rgba(99, 102, 241, 0.05)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                                <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                                    <div style={{ background: 'var(--accent-primary)', padding: '10px', borderRadius: '12px' }}>
                                        <Briefcase color="white" size={24} />
                                    </div>
                                    <div>
                                        <h4 style={{ marginBottom: '8px' }}>Direct Employer Feedback</h4>
                                        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>"We hired 4 students from the Senior Capstone because their Curriculum Match against our tech stack (Next.js/Postgres) was 95% Verified."</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="engine-visual animate-fade-up delay-1">
                            <div className="glass-panel" style={{ padding: '0', background: 'var(--bg-card)' }}>
                                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <div className="status-dot status-online"></div>
                                        <span style={{ fontWeight: '600' }}>Employer Portal: Recruiting Dashboard</span>
                                    </div>
                                </div>
                                <div style={{ padding: '24px' }}>
                                    <div style={{ background: '#000', borderRadius: '12px', border: '1px solid var(--border-color)', padding: '16px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Top Matched Talent (UT System)</span>
                                            <span style={{ fontSize: '0.7rem', color: 'var(--success)' }}>LIVE FEED</span>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                                                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(45deg, #6366f1, #a855f7)' }}></div>
                                                    <div>
                                                        <div style={{ fontSize: '0.85rem', fontWeight: '600' }}>Student ID: #UT-4402</div>
                                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>CS Major • Data Science Elective</div>
                                                    </div>
                                                </div>
                                                <div style={{ textAlign: 'right' }}>
                                                    <div style={{ color: 'var(--success)', fontWeight: '700', fontSize: '1rem' }}>96% Match</div>
                                                    <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Verified via Project Repo #55</div>
                                                </div>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', opacity: 0.7 }}>
                                                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(45deg, #10b981, #3b82f6)' }}></div>
                                                    <div>
                                                        <div style={{ fontSize: '0.85rem', fontWeight: '600' }}>Student ID: #UT-1290</div>
                                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>IS Major • Cloud Admin Elective</div>
                                                    </div>
                                                </div>
                                                <div style={{ textAlign: 'right' }}>
                                                    <div style={{ color: 'var(--success)', fontWeight: '700', fontSize: '1rem' }}>92% Match</div>
                                                    <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Verified via AWS Lab Docs</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW Phase 4] Executive Placement Analytics */}
            <section className="executive-kpis" style={{ padding: '100px 0', background: 'var(--bg-primary)', borderTop: '1px solid var(--border-color)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient-green">Executive Placement Analytics</h2>
                        <p className="subtitle">Drive institutional prestige by optimizing the metrics that define your university rankings.</p>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginTop: '48px' }}>
                        <div className="b2b-card animate-fade-up delay-1" style={{ borderTop: '4px solid var(--accent-primary)' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '12px' }}>Placement Velocity</div>
                            <div style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '8px' }}>-3.2 Months</div>
                            <div style={{ fontSize: '0.9rem', color: 'var(--success)' }}>Avg. reduction in time-to-hire.</div>
                        </div>
                        <div className="b2b-card animate-fade-up delay-2" style={{ borderTop: '4px solid var(--success)' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '12px' }}>Starting Salary Lift</div>
                            <div style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '8px' }}>+$12,400</div>
                            <div style={{ fontSize: '0.9rem', color: 'var(--success)' }}>Avg. increase for Thara-native students.</div>
                        </div>
                        <div className="b2b-card animate-fade-up delay-3" style={{ borderTop: '4px solid var(--warning)' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '12px' }}>Institutional Prestige</div>
                            <div style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '8px' }}>Top 15%</div>
                            <div style={{ fontSize: '0.9rem', color: 'var(--warning)' }}>US News "Career Services" Ranking.</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW] Early Pilot Data */}
            <section className="pilot-metrics-section" style={{ padding: '80px 0', background: 'var(--bg-card)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2>Validating the B2B Pipeline</h2>
                        <p className="subtitle">Early performance metrics from our closed university ecosystem pilot.</p>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginTop: '40px' }}>
                        <div className="b2b-card text-center animate-fade-up delay-1" style={{ border: '1px solid var(--accent-primary)', background: 'rgba(99, 102, 241, 0.05)' }}>
                            <div style={{ fontSize: '3.5rem', fontWeight: '800', color: 'var(--accent-primary)', marginBottom: '8px' }}>87%</div>
                            <div style={{ color: 'var(--text-primary)', fontWeight: '600' }}>Drop in Rejection Due to</div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>ATS JSON Parsing Errors.</div>
                        </div>
                        <div className="b2b-card text-center animate-fade-up delay-2" style={{ border: '1px solid var(--success)', background: 'rgba(16, 185, 129, 0.05)' }}>
                            <div style={{ fontSize: '3.5rem', fontWeight: '800', color: 'var(--success)', marginBottom: '8px' }}>300+</div>
                            <div style={{ color: 'var(--text-primary)', fontWeight: '600' }}>Hours Saved Per Semester</div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>By Tier-1 Career Counselors.</div>
                        </div>
                        <div className="b2b-card text-center animate-fade-up delay-3" style={{ border: '1px solid var(--warning)', background: 'rgba(245, 158, 11, 0.05)' }}>
                            <div style={{ fontSize: '3.5rem', fontWeight: '800', color: 'var(--warning)', marginBottom: '8px' }}>100%</div>
                            <div style={{ color: 'var(--text-primary)', fontWeight: '600' }}>Traceable Verification</div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>To Official Course Syllabi.</div>
                        </div>
                    </div>
                    
                    <div className="testimonial animate-fade-up delay-4" style={{ marginTop: '40px', padding: '32px', background: 'var(--bg-secondary)', borderRadius: '16px', borderLeft: '4px solid var(--accent-primary)', fontStyle: 'italic', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                        "By automating the tedious PDF profile review layer, Thara finally allowed our counseling staff to spend 100% of their time building targeted recruiter pipelines and employer relationships instead of fixing Word Document margins." 
                        <div style={{ marginTop: '16px', fontWeight: '600', color: 'var(--text-primary)', fontStyle: 'normal' }}>— Director of Career Services (Beta Partner)</div>
                    </div>
                </div>
            </section>
            {/* B2B Enterprise CTA */}
            <section className="cta-section" style={{ paddingBottom: '80px' }}>
                <div className="container text-center animate-fade-up">
                    <div style={{ maxWidth: '800px', margin: '0 auto', background: 'linear-gradient(180deg, rgba(16, 185, 129, 0.1) 0%, var(--bg-secondary) 100%)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '48px 32px', borderRadius: '24px' }}>
                        <h2 style={{ fontSize: '2.2rem', marginBottom: '16px' }}>Secure Your White-Label Enterprise License</h2>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', fontSize: '1.05rem', lineHeight: '1.6' }}>
                            Available as a recurring annual enterprise license ($50,000 - $150,000+). White-label Thara directly into your university portal and instantly raise your post-graduation employment KPIs—the metric that drives your university's institutional prestige and future tuition revenue.
                        </p>
                        <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
                            <button className="btn-primary" style={{ background: 'var(--success)', color: '#000', border: 'none' }}>
                                Request Institutional Demo
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Competitive Analysis Section */}
            <CompetitiveTable
                title="Institutional Competitive Analysis"
                subtitle="Why JobsProof is the gold standard for data-driven departments."
                competitorName="Generic Career Portals"
                rows={[
                    { feature: 'Data Source', us: 'Verified Syllabus & Project Repos', them: 'Self-Reported Resumes' },
                    { feature: 'Audit Readiness', us: 'One-Click Accreditation Evidence', them: 'Manual Document Hunting' },
                    { feature: 'Market Alignment', us: 'Real-time Regional Skill Mapping', them: 'Stale Annual Reports' },
                    { feature: 'ROI Tracking', us: 'Longitudinal Course-to-Career Path', them: 'Aggregated Salary Averages' }
                ]}
            />

            <FAQ
                title="University FAQ"
                items={[
                    { question: "How much effort is required for implementation?", answer: "Near-zero. We integrate directly with LMS export formats (Canvas/Blackboard) or ingested department syllabi. We don't require manual tagging from faculty or IT." },
                    { question: "Does this replace my human career counseling staff?", answer: "Absolutely not. Thara replaces the rote, tedious work of document formatting and initial gap analysis. Your human staff is elevated to 'Tier-2' functions—like deep emotional counseling, alumni networking, and direct employer relationship building." },
                    { question: "How does Thara assist with ABET/AACSB accreditation?", answer: "Thara functions as an automated 'Evidence Vault.' By tracking student outcomes against specific syllabus learning objectives, we generate pre-formatted evidence dossiers that show exactly how your department achieves its educational objectives." },
                    { question: "Is Thara FERPA compliant?", answer: "Yes. Our architecture utilizes a 'Data Minimization' strategy where PII is logically segregated, and all institutional data is encrypted with AES-256 at rest. We provide clear audit logs for university IT departments." }
                ]}
            />

        </>
    );
}
