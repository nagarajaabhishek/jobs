import { AlertTriangle, XCircle, Search, ShieldCheck } from 'lucide-react';
import '../index.css';

const detailedData = [
    {
        platform: 'Handshake',
        strategy: 'Employers (Filtering & volume)',
        mechanism: '"Best Match" algorithm on basic qualifications',
        trustDeficit: 'Institutional Inertia: Built for employers to filter out, not for students to improve.',
        valueGap: 'No prescriptive gap analysis. Values access over improvement.',
        icon: <Search size={18} />
    },
    {
        platform: 'JobRight.ai',
        strategy: 'Students (Speed & automated rewriting)',
        mechanism: 'AI-Agent extracting and over-optimizing keywords',
        trustDeficit: 'Trust Deficit: High hallucination risk. Fakes evidence, creating recruiter AI-spam blacklists.',
        valueGap: 'Zero academic context or verified gap analysis.',
        icon: <AlertTriangle size={18} color="var(--warning)" />
    },
    {
        platform: 'Simplify',
        strategy: 'Students (Form-filling automation)',
        mechanism: 'Keyword overlap and basic profile mapping',
        trustDeficit: 'Shallow Context: Treats simple scripts like major thesis projects.',
        valueGap: 'Autofill extension only, zero value for career readiness tracking.',
        icon: <XCircle size={18} color="var(--warning)" />
    },
    {
        platform: 'LinkedIn / Indeed',
        strategy: 'Mass Market / Professionals',
        mechanism: 'Simple Title parsing & paid "Top Applicant" tags',
        trustDeficit: 'Domain Blindness & High Noise: Rife with ghost jobs and broad suggestions.',
        valueGap: 'Networking capabilities, but no actual skill validation.',
        icon: <XCircle size={18} />
    },
    {
        platform: 'JobsProof.com',
        strategy: 'Students & Universities (Curriculum ROI)',
        mechanism: 'Verification-Based Matching mapped to graded syllabi',
        trustDeficit: 'Authenticity Moat: Eliminates hallucinations by gating skills against verified projects.',
        valueGap: 'Deep Prescriptive Gap Analysis. Tells you exactly what to study.',
        icon: <ShieldCheck size={20} color="var(--success)" />,
        isJobsProof: true
    }
];

export default function DetailedCompetitiveMatrix() {
    return (
        <section className="detailed-matrix-section" style={{ padding: '80px 0', background: 'var(--bg-card)' }}>
            <div className="container">
                <div className="section-header text-center animate-fade-up">
                    <h2 className="text-gradient">The Competitive Landscape</h2>
                    <p className="subtitle" style={{ maxWidth: '800px', margin: '0 auto' }}>
                        When it comes to your career, keyword spamming and hallucinations ruin trust. See how JobsProof's syllabus-driven engine compares to legacy tools and AI wrappers like JobRight.
                    </p>
                </div>

                <div className="table-wrapper animate-fade-up delay-1" style={{ overflowX: 'auto', marginTop: '40px' }}>
                    <table style={{ width: '100%', minWidth: '900px', borderCollapse: 'collapse', textAlign: 'left', background: 'var(--bg-secondary)', borderRadius: '16px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
                        <thead>
                            <tr style={{ background: 'rgba(99, 102, 241, 0.05)', borderBottom: '1px solid var(--border-color)' }}>
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>Platform</th>
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>Primary Strategy</th>
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>Matching Mechanism</th>
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>Trust Deficits & Issues</th>
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>The Value "Gap"</th>
                            </tr>
                        </thead>
                        <tbody>
                            {detailedData.map((row, idx) => (
                                <tr key={idx} style={{
                                    borderBottom: idx === detailedData.length - 1 ? 'none' : '1px solid var(--border-color)',
                                    background: row.isJobsProof ? 'rgba(16, 185, 129, 0.05)' : 'transparent',
                                    transition: 'background 0.3s ease'
                                }}>
                                    <td style={{ padding: '20px', fontWeight: row.isJobsProof ? '700' : '500', color: row.isJobsProof ? 'var(--success)' : 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        {row.icon}
                                        {row.platform}
                                        {row.isJobsProof && <span style={{ fontSize: '0.65rem', padding: '2px 6px', background: 'var(--success)', color: '#000', borderRadius: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Our Engine</span>}
                                    </td>
                                    <td style={{ padding: '20px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{row.strategy}</td>
                                    <td style={{ padding: '20px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{row.mechanism}</td>
                                    <td style={{ padding: '20px', fontSize: '0.9rem', color: row.isJobsProof ? 'var(--success)' : 'var(--warning)', fontWeight: row.isJobsProof ? '600' : '400' }}>{row.trustDeficit}</td>
                                    <td style={{ padding: '20px', fontSize: '0.9rem', color: row.isJobsProof ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: row.isJobsProof ? '600' : '400' }}>{row.valueGap}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
}
