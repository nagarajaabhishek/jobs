import { Network, Database, BrainCircuit, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ArchitectureSection() {
    return (
        <section className="architecture-teaser-section" style={{ padding: '80px 0', background: 'var(--bg-card)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
            <div className="container">
                <div className="section-header text-center animate-fade-up">
                    <h2 className="text-gradient">Powered by Agentic Intelligence</h2>
                    <p className="subtitle" style={{ maxWidth: '800px', margin: '0 auto' }}>
                        JobsProof is not just a UI wrapper. It's a high-throughput LLM pipeline orchestrating dual-model evaluation, ATS ingestion, and prescriptive analytics.
                    </p>
                </div>

                <div className="teaser-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginTop: '40px' }}>

                    {/* Tech Stack Card */}
                    <div className="feature-card animate-fade-up delay-1" style={{ background: 'var(--bg-secondary)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                        <div className="feature-icon" style={{ background: 'rgba(99, 102, 241, 0.1)' }}>
                            <Database size={24} color="var(--accent-primary)" />
                        </div>
                        <h3 style={{ fontSize: '1.2rem', marginBottom: '12px' }}>Modern Tech Stack</h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '16px' }}>Built for scale using React/Vite on the frontend, and a robust Python-based LangGraph state machine backend.</p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            <span className="skill-tag" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>React + Vite</span>
                            <span className="skill-tag" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>Python Agent</span>
                            <span className="skill-tag" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>LangGraph</span>
                        </div>
                    </div>

                    {/* App Features Card */}
                    <div className="feature-card animate-fade-up delay-2" style={{ background: 'var(--bg-secondary)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                        <div className="feature-icon" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
                            <BrainCircuit size={24} color="var(--success)" />
                        </div>
                        <h3 style={{ fontSize: '1.2rem', marginBottom: '12px' }}>Dual-Model Strategy</h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '16px' }}>Utlilizing Gemini 2.5 Flash-Lite for ultra-fast, low-cost sourcing logic, and Gemini 2.0 Flash for deep ATS evaluations via an OpenRouter Unified Cloud Bridge.</p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            <span className="skill-tag" style={{ fontSize: '0.75rem', padding: '4px 8px', borderColor: 'var(--success)', color: 'var(--success)' }}>Gemini 2.5 / 2.0</span>
                            <span className="skill-tag" style={{ fontSize: '0.75rem', padding: '4px 8px', borderColor: 'var(--success)', color: 'var(--success)' }}>OpenRouter Bridge</span>
                        </div>
                    </div>

                    {/* Architecture Teaser Card */}
                    <div className="feature-card animate-fade-up delay-3" style={{ background: 'var(--bg-secondary)', border: '1px solid rgba(245, 158, 11, 0.2)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                            <div className="feature-icon" style={{ background: 'rgba(245, 158, 11, 0.1)' }}>
                                <Network size={24} color="var(--warning)" />
                            </div>
                            <h3 style={{ fontSize: '1.2rem', marginBottom: '12px' }}>End-to-End Pipeline</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>A 4-stage automated pipeline from target-driven ATS ingestion, context intelligence injection, deep gap evaluation, to Google Sheets SSOT harvesting.</p>
                        </div>
                        <Link to="/architecture" style={{ marginTop: '20px', textDecoration: 'none' }}>
                            <button className="btn-secondary w-full" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '12px', fontSize: '0.95rem', borderColor: 'var(--warning)', color: 'var(--warning)' }}>
                                View Full Architecture <ArrowRight size={16} />
                            </button>
                        </Link>
                    </div>

                </div>
            </div>
        </section>
    );
}
