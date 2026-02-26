import { useState, useEffect } from 'react';
import { BarChart3, Building2, GraduationCap, ArrowRight, Briefcase } from 'lucide-react';
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
                        <h1 style={{ fontSize: '3.5rem', lineHeight: '1.2', marginBottom: '24px' }}>Close the "Black Box" of <span style={{ color: 'var(--success)' }}>Student Success.</span></h1>
                        <p>Stop guessing why graduates aren't getting hired. Get actionable data to prove your curriculum's ROI with <strong>JobsProof.com</strong>, update syllabi dynamically, and simplify accreditation reporting.</p>

                        <div className="cta-group">
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
                            <GraduationCap size={32} className="b2b-icon" />
                            <h3>Accreditation Data</h3>
                            <p>Generate automated reports for ABET or AACSB accreditation workflows based on verified student skill mastery against real-world job data.</p>
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

            {/* [NEW] Accreditation Evidence Dashboard */}
            <section className="accreditation-section" style={{ padding: '80px 0', background: 'var(--bg-secondary)' }}>
                <div className="container">
                    <div className="engine-grid" style={{ alignItems: 'center' }}>
                        <div className="engine-visual animate-fade-up">
                            <div className="glass-panel" style={{ padding: '0', background: 'var(--bg-card)' }}>
                                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Building2 size={18} color="var(--success)" />
                                        <span style={{ fontWeight: '600' }}>{activeDept === 'business' ? 'AACSB' : activeDept === 'science' ? 'SACS' : 'ABET'} Audit Evidence</span>
                                    </div>
                                    <span style={{ fontSize: '0.75rem', background: '#000', padding: '4px 8px', borderRadius: '4px', color: 'var(--text-secondary)' }}>ID: #501-EVD</span>
                                </div>
                                <div style={{ padding: '24px 20px' }}>
                                    {currentData.evidence.map((ev, idx) => (
                                        <div key={idx} className={`evidence-block ${idx > 0 ? 'mt-4' : ''}`} style={idx > 0 ? { opacity: 0.6 } : {}}>
                                            <div className="evidence-header">Requirement: {ev.req}</div>
                                            <div className="evidence-source">Source: {ev.source}</div>
                                            <div className="evidence-data">{ev.data}</div>
                                            <div className="evidence-status">READY FOR EXPORT</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div className="engine-text animate-fade-up delay-1">
                            <h2>Automated Audit Readiness</h2>
                            <p className="subtitle">Stop hunting for student work samples. We map verified proof of work directly to your accreditation requirements.</p>
                            <ul style={{ listStyle: 'none', padding: '0', marginTop: '24px' }}>
                                <li style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                                    <div style={{ color: 'var(--success)' }}>✓</div>
                                    <div><strong>ABET/AACSB Ready:</strong> One-click export of student project samples mapped to specific learning outcomes.</div>
                                </li>
                                <li style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                                    <div style={{ color: 'var(--success)' }}>✓</div>
                                    <div><strong>Verified Mastery:</strong> Proof comes from GitHub repos and project docs, not just grades.</div>
                                </li>
                                <li style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                                    <div style={{ color: 'var(--success)' }}>✓</div>
                                    <div><strong>Longitudinal ROI:</strong> Track employment success of students who mastered specific competencies.</div>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* [NEW] XY Strategic Graph Section */}
            <section className="xy-analysis-section" style={{ padding: '100px 0', background: 'var(--bg-primary)' }}>
                <div className="container">
                    <div className="section-header text-center animate-fade-up">
                        <h2 className="text-gradient">Strategic XY Positioning</h2>
                        <p className="subtitle">High-fidelity data with near-zero manual overhead.</p>
                    </div>

                    <div className="xy-graph-wrapper animate-fade-up delay-1">
                        <div className="xy-graph">
                            {/* Y-Axis (Data Granularity) */}
                            <div className="y-axis">
                                <div className="y-label">High Data Granularity</div>
                                <div className="y-arrow"></div>
                                <div className="y-label-sub">Low Data Granularity</div>
                            </div>

                            {/* X-Axis (Manual Audit Effort) */}
                            <div className="x-axis">
                                <div className="x-label-sub">High Manual Effort</div>
                                <div className="x-arrow"></div>
                                <div className="x-label">Low Manual Effort</div>
                            </div>

                            {/* Data Points */}
                            <div className="point-us pulsate-point">
                                <div className="point-label">JobsProof</div>
                            </div>
                            <div className="point-fair" style={{ bottom: '80%', left: '20%' }}>
                                <div className="point-label" style={{ whiteSpace: 'nowrap' }}>Manual Faculty Audits</div>
                            </div>
                            <div className="point-survey" style={{ bottom: '30%', left: '70%' }}>
                                <div className="point-label">Handshake</div>
                            </div>
                            <div className="point-survey" style={{ bottom: '25%', left: '60%', background: 'var(--text-secondary)' }}>
                                <div className="point-label">Symplicity</div>
                            </div>
                            <div className="point-survey" style={{ bottom: '35%', left: '65%', background: 'var(--text-secondary)' }}>
                                <div className="point-label">12Twenty</div>
                            </div>
                            <div className="point-handshake" style={{ bottom: '15%', left: '85%' }}>
                                <div className="point-label" style={{ whiteSpace: 'nowrap' }}>LinkedIn / Generic Boards</div>
                            </div>
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
