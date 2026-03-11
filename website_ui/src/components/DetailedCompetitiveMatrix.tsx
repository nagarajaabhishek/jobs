import { AlertTriangle, XCircle, Search, ShieldCheck } from 'lucide-react';
import '../index.css';

const detailedData = [
    {
        platform: 'Handshake',
        strategy: 'Employers (Filtering)',
        mechanism: 'Basic Qualifications',
        trustDeficit: 'Low Trust: Employers treat as a low-signal filtering tool.',
        valueGap: 'No skill validation or prescriptive feedback.',
        syllabus: false,
        evidence: false,
        icon: <Search size={18} />
    },
    {
        platform: 'JobRight.ai',
        strategy: 'Students (Rewriting)',
        mechanism: 'AI Keyword Stuffing',
        trustDeficit: 'Critical: Creating recruiter blacklists for AI-spam.',
        valueGap: 'Fakes experience, destroying long-term applicant credit.',
        syllabus: false,
        evidence: false,
        icon: <AlertTriangle size={18} color="var(--warning)" />
    },
    {
        platform: 'Simplify',
        strategy: 'Students (Autofill)',
        mechanism: 'Browser Profile Mapping',
        trustDeficit: 'Shallow: No context on how skills were built.',
        valueGap: 'Zero value for career readiness or skill roadmaps.',
        syllabus: false,
        evidence: false,
        icon: <XCircle size={18} color="var(--warning)" />
    },
    {
        platform: 'LinkedIn / Indeed',
        strategy: 'Mass Market',
        mechanism: 'Paid Applicant Tags',
        trustDeficit: 'Noisy: Dominated by ghost jobs and AI-noise.',
        valueGap: 'Broad networking, but zero institutional verification.',
        syllabus: false,
        evidence: false,
        icon: <XCircle size={18} />
    },
    {
        platform: 'JobsProof.com',
        strategy: 'Students & Universities',
        mechanism: 'Syllabus-Anchored verification',
        trustDeficit: 'Absolute: Skills are gated by institutional graded proof.',
        valueGap: 'Eliminates guesswork. Tells you specifically what to study.',
        syllabus: true,
        evidence: true,
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
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>Syllabus Sync</th>
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>AI-Verified Proof</th>
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>Trust Level</th>
                                <th style={{ padding: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>The Value Gap</th>
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
                                    <td style={{ padding: '20px', textAlign: 'center' }}>
                                        {row.syllabus ? <ShieldCheck size={18} color="var(--success)" /> : <XCircle size={18} color="var(--warning)" style={{ opacity: 0.3 }} />}
                                    </td>
                                    <td style={{ padding: '20px', textAlign: 'center' }}>
                                        {row.evidence ? <ShieldCheck size={18} color="var(--success)" /> : <XCircle size={18} color="var(--warning)" style={{ opacity: 0.3 }} />}
                                    </td>
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
