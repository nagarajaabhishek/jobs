import { useEffect } from 'react';
import { Database, Network, BrainCircuit, ShieldCheck, GitBranch, ArrowRight, Activity, Globe, LayoutTemplate } from 'lucide-react';
import Mermaid from '../components/Mermaid';
import '../index.css';

const pipelineChart = `
flowchart TD
    %% Phase 0: Inputs
    subgraph Inputs["Base Configurations"]
        H[("University Syllabus YAML")]
        I[("Master Profile YAML")]
        T[("LaTeX Base Templates")]
    end

    %% Phase 1: Sourcing
    subgraph Sourcing["Phase 1: Sourcing & Filtering"]
        A["Direct ATS Scrapers"]
        B["JobSpy / Aggregators"]
        A --> C{"H1B Sponsorship Probe"}
        B --> C
        C -- "No" --> Z(("Drop"))
        C -- "Yes" --> D{"Location Priority Router"}
        D -- "Non-Target" --> Z
        D -- "Target Hubs" --> E{"Gemini 2.5 Flash-Lite"}
        E -- "Lacks Keywords" --> Z
        E -- "Valid Jobs" --> F[("Local JSON Cache")]
    end

    %% The Core Cache
    E -- "Valid Jobs" --> F[("Local JSON JD Cache (Storage)")]

    %% Phase 2: Context
    subgraph Injection["Phase 2: Context Injection"]
        F --> G["LangGraph State Machine"]
        H --> G
        I --> G
    end

    %% Phase 3: AI Eval
    subgraph Evaluation["Phase 3: Deep AI Evaluation"]
        G --> J["Gemini 2.0 Flash Rubric"]
        J -. "Fallback" .-> K["OpenRouter Unified Bridge"]
        J & K --> L(["Match Score %"])
        J & K --> M(["Prescriptive Gap Analysis"])
    end

    %% Phase 4: Artifact Generation (Resume_Agent)
    subgraph Artifacts["Phase 4: Artifact Generation (Resume_Agent)"]
        W[("Antigravity Master Rules & Workflows")] -. "Enforces XYZ Pattern" .-> O
        L & M --> O["Python Tailoring Engine"]
        T --> O
        O --> P[("LaTeX Compiled PDF Resume")]
        O --> Q[("LaTeX Compiled Cover Letter")]
    end

    %% Phase 5: UI & Distribution
    subgraph Distribution["Phase 5: Product Interfaces"]
        L & M --> N[("Google Sheets SSOT")]
        N --> U["JobsProof B2C (Student Feed)"]
        N --> V["JobsProof B2B (University Analytics)"]
        
        P & Q --> S["Auto-Apply Automation"]
    end

    classDef source fill:#1e1e24,stroke:#6366f1,stroke-width:2px,color:#fff
    classDef filter fill:#0d1117,stroke:#14b8a6,stroke-width:2px,color:#fff
    classDef agent fill:#0d1117,stroke:#10b981,stroke-width:2px,color:#fff
    classDef eval fill:#0d1117,stroke:#f59e0b,stroke-width:2px,color:#fff
    classDef generator fill:#0d1117,stroke:#a855f7,stroke-width:2px,color:#fff
    classDef ui fill:#1e1e24,stroke:#ec4899,stroke-width:2px,color:#fff
    classDef db fill:#0d1117,stroke:#3b82f6,stroke-width:2px,color:#fff
    classDef cache fill:#0f172a,stroke:#38bdf8,stroke-width:3px,color:#fff,stroke-dasharray: 5 5
    classDef drop fill:#2d1b1b,stroke:#ef4444,stroke-width:2px,color:#fca5a5

    class A,B source
    class C,D,E filter
    class G agent
    class J,K eval
    class O,P,Q generator
    class S,U,V ui
    class H,I,T,N,W db
    class F cache
    class Z drop
`;

export default function Architecture() {
    useEffect(() => {
        document.title = "Architecture | JobsProof.com";
        window.scrollTo(0, 0);
    }, []);

    return (
        <div className="architecture-page" style={{ paddingTop: '80px', paddingBottom: '100px' }}>
            {/* Hero Section */}
            <section className="container">
                <div className="section-header text-center animate-fade-up">
                    <div className="student-tag" style={{ margin: '0 auto 24px auto', display: 'inline-flex' }}>
                        <Network size={16} /> Technical Deep Dive
                    </div>
                    <h1 style={{ fontSize: '3rem', marginBottom: '24px' }}>
                        The <span className="text-gradient">Agentic Pipeline</span> Engine
                    </h1>
                    <p className="subtitle" style={{ maxWidth: '800px', margin: '0 auto', fontSize: '1.2rem', lineHeight: '1.6' }}>
                        JobsProof is powered by a high-throughput, dual-model LLM architecture. We eliminated keyword matching in favor of deterministic gap analysis and strategic go-to-market analytics.
                    </p>
                </div>
            </section>

            {/* Pipeline Visualization */}
            <section className="container" style={{ marginTop: '80px' }}>
                <div className="glass-panel animate-fade-up delay-1" style={{ padding: '40px', background: 'var(--bg-secondary)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
                        <Activity size={24} color="var(--accent-primary)" />
                        <h2 style={{ fontSize: '1.5rem', margin: '0' }}>Real-Time Data Flow</h2>
                    </div>

                    <div className="pipeline-flow" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                        {/* Layer 1 */}
                        <div className="flow-step" style={{ display: 'flex', gap: '20px', alignItems: 'center', background: 'var(--bg-card)', padding: '24px', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
                            <div className="step-number" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-primary)', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', fontWeight: 'bold' }}>1</div>
                            <div style={{ flex: 1 }}>
                                <h3 style={{ fontSize: '1.2rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    High-Throughput Sourcing Layer
                                    <span style={{ fontSize: '0.7rem', padding: '2px 8px', background: 'rgba(245, 158, 11, 0.1)', color: 'var(--warning)', borderRadius: '4px' }}>Gemini 2.5 Flash-Lite</span>
                                </h3>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '0' }}>
                                    We rely on Python Agentic Scrapers (JobSpy, Custom ATS scrapers like Lever/Greenhouse) to ingest raw job data, immediately discarding irrelevant roles using ultra-low-cost "sniffing".
                                </p>
                            </div>
                        </div>

                        {/* Layer 2 */}
                        <div className="flow-step flex" style={{ paddingLeft: '24px' }}><ArrowRight size={24} color="var(--border-color)" style={{ transform: 'rotate(90deg)' }} /></div>

                        <div className="flow-step" style={{ display: 'flex', gap: '20px', alignItems: 'center', background: 'var(--bg-card)', padding: '24px', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
                            <div className="step-number" style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-primary)', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', fontWeight: 'bold' }}>2</div>
                            <div style={{ flex: 1 }}>
                                <h3 style={{ fontSize: '1.2rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    Context Injection
                                    <span style={{ fontSize: '0.7rem', padding: '2px 8px', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', borderRadius: '4px' }}>LangGraph Validated</span>
                                </h3>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '0' }}>
                                    A Python-based state machine parses the structured university syllabus and master configurations (YAML). It builds a holistic profile of the applicant's real-world capabilities.
                                </p>
                            </div>
                        </div>

                        {/* Layer 3 */}
                        <div className="flow-step flex" style={{ paddingLeft: '24px' }}><ArrowRight size={24} color="var(--border-color)" style={{ transform: 'rotate(90deg)' }} /></div>

                        <div className="flow-step" style={{ display: 'flex', gap: '20px', alignItems: 'center', background: 'var(--bg-card)', padding: '24px', borderRadius: '16px', border: '1px solid rgba(16, 185, 129, 0.3)', boxShadow: '0 0 20px rgba(16, 185, 129, 0.05)' }}>
                            <div className="step-number" style={{ background: 'var(--success)', color: '#fff', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', fontWeight: 'bold', boxShadow: '0 0 15px var(--success)' }}>3</div>
                            <div style={{ flex: 1 }}>
                                <h3 style={{ fontSize: '1.2rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    Deep Evaluation Engine
                                    <span style={{ fontSize: '0.7rem', padding: '2px 8px', background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-primary)', borderRadius: '4px' }}>Gemini 2.0 Flash / OpenRouter</span>
                                </h3>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '0' }}>
                                    The core intelligence. A sophisticated 2.0 Rubric evaluates the applicant's verified proof-of-work against the ATS requirements, generating a 0-100 deterministic Conviction Score and identifying exact skill gaps.
                                </p>
                            </div>
                        </div>

                    </div>
                </div>
            </section>

            {/* Mermaid Architecture Flow */}
            <section className="container" style={{ marginTop: '80px' }}>
                <div className="glass-panel animate-fade-up delay-2" style={{ padding: '60px 40px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{ marginBottom: '40px', textAlign: 'center' }}>
                        <h2 style={{ fontSize: '1.8rem', marginBottom: '16px' }}>System Architecture Map</h2>
                        <p style={{ color: 'var(--text-secondary)', maxWidth: '600px' }}>A visual representation of the dual-model strategy, routing logic, and state machine validation.</p>
                    </div>

                    <div className="mermaid-render-box" style={{ width: '100%', maxWidth: '1200px', background: 'rgba(0,0,0,0.4)', padding: '3vw', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <Mermaid chart={pipelineChart} />
                    </div>
                </div>
            </section>

            {/* Core Features Grid */}
            <section className="container" style={{ marginTop: '100px' }}>
                <h2 style={{ fontSize: '2rem', textAlign: 'center', marginBottom: '60px' }}>Architectural Pillars</h2>

                <div className="feature-grid">
                    <div className="feature-card animate-fade-up delay-1">
                        <div className="feature-icon"><LayoutTemplate size={24} /></div>
                        <h3>React + Vite Interface</h3>
                        <p>The student-facing App is built on a highly responsive React/Vite stack. It utilizes modern glassmorphism design principles, Lucide icons, and dynamic routing to provide a seamless B2C experience.</p>
                    </div>

                    <div className="feature-card animate-fade-up delay-2">
                        <div className="feature-icon"><BrainCircuit size={24} /></div>
                        <h3>Dual-Model Strategy</h3>
                        <p>By balancing Gemini 2.5 Flash-Lite for bulk filtering and Gemini 2.0 Flash via OpenRouter for complex matching, the pipeline minimizes cost while maximizing evaluation detail and rate-limit resilience.</p>
                    </div>

                    <div className="feature-card animate-fade-up delay-3">
                        <div className="feature-icon"><Globe size={24} /></div>
                        <h3>B2B Analytics Go-to-Market</h3>
                        <p>Beyond student matchmaking, the LLM aggregate data is structured to provide institutional-grade curriculum analytics to university partners, mapping academic syllabus outcomes directly to industry trend shifts.</p>
                    </div>

                    <div className="feature-card animate-fade-up delay-4">
                        <div className="feature-icon"><LayoutTemplate size={24} /></div>
                        <h3>LaTeX Resume Engine</h3>
                        <p>We decouple data from design. The Python pipeline uses your Master Profile (YAML) to dynamically inject matching keywords into a structural LaTeX template (.cls), guaranteeing 90%+ parse rates across every standard ATS.</p>
                    </div>

                    <div className="feature-card animate-fade-up delay-5">
                        <div className="feature-icon"><ShieldCheck size={24} /></div>
                        <h3>Unified Cloud Bridge</h3>
                        <p>A robust API fallback system using OpenRouter guarantees uptime. If a primary LLM endpoint is throttled, the evaluation state machine instantly reroutes to an alternative model.</p>
                    </div>

                    <div className="feature-card animate-fade-up delay-6">
                        <div className="feature-icon"><Database size={24} /></div>
                        <h3>Local JSON JD Caching</h3>
                        <p>Full Job Descriptions are cached locally to avoid cluttering downstream database clients (Google Sheets), keeping the SSOT clean and hyper-focused on prescriptive analytics.</p>
                    </div>

                    <div className="feature-card animate-fade-up delay-6">
                        <div className="feature-icon"><GitBranch size={24} /></div>
                        <h3>Stateful Pipeline</h3>
                        <p>Agent logic is segmented. Separate tools handle sponsorship probing, 80/20 location prioritization, and keyword expansion without cross-contaminating the primary Match Scoring Rubric.</p>
                    </div>
                </div>
            </section>
        </div>
    );
}
