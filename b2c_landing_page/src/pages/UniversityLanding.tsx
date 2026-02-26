import { useState, useEffect } from 'react';
import { BarChart3, Building2, ArrowRight, Briefcase, XCircle, ShieldCheck } from 'lucide-react';
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
            <section className="hero-section" style={{ background: 'radial-gradient(ellipse at top, rgba(16, 185, 129, 0.1) 0%, var(--bg-primary) 70%)' }}>
                <div className="container text-center">
                    <div className="hero-content animate-fade-up" style={{ margin: '0 auto', maxWidth: '800px' }}>
                        <div className="b2b-badge" style={{ display: 'inline-block', margin: '0 auto 24px auto' }}>For Universities & Dept Heads</div>
                        <h1 style={{ fontSize: '3.5rem', lineHeight: '1.2', marginBottom: '24px' }}>Prove the exact ROI of your <span style={{ color: 'var(--success)' }}>Curriculum.</span></h1>
                        <p>Employers are drowning in AI-generated resume spam. Transform your syllabi into verified talent profiles that top tech companies actually trust.</p>

                        <div className="cta-group" style={{ justifyContent: 'center' }}>
                            <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--success)', color: '#000' }}>
                                Request Department Demo <ArrowRight size={18} />
                            </button>
                            <button className="btn-secondary">View Sample Analytics</button>
                        </div>
                    </div>
                </div>
            </section>

            {/* University B2B Section */}
            <section className="b2b-section" style={{ paddingTop: '60px' }}>
                <div className="b2b-bg-glow"></div>
                <div className="container">
                    <div className="b2b-grid" style={{ marginTop: '0' }}>
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
                            <ShieldCheck size={32} className="b2b-icon" />
                            <h3>Rebuild Employer Trust</h3>
                            <p>Handshake is drowning in AI hallucinations. We act as a firewall, guaranteeing employers that your graduates' listed skills are deterministically proven.</p>
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
                    { question: "Is JobsProof FERPA compliant?", answer: "Yes. We use a 'Data Minimization' strategy—extracting skill signatures instead of storing sensitive PII. Our infrastructure is built to exceed FERPA and SOC2 standards, using HSTS and AES-256 encryption at rest." },
                    { question: "How does the platform handle DNS security?", answer: "Our professional infrastructure on jobsproof.com utilizes DNSSEC (Domain Name System Security Extensions) and HSTS to prevent protocol-level attacks and ensure students always connect to a verified, encrypted environment." },
                    { question: "How much effort is required for implementation?", answer: "Near-zero. We integrate directly with LMS export formats (Canvas/Blackboard) or ingested department syllabi. We don't require manual tagging from faculty or IT." },
                    { question: "What is the cost for a department-wide pilot?", answer: "Pilots are currently subsidized for UT System programs. For other institutions, we offer a flat-rate 'Market Alignment Audit' or a per-student licensing model based on department size." }
                ]}
            />

        </>
    );
}
