import { Link } from 'react-router-dom';
import { Search, Scale, FileEdit, BookOpen } from 'lucide-react';

const agents = [
  {
    title: 'Sourcing',
    body: 'JobSpy, boards, ATS and community scrapers → sheet rows with verified JDs where possible.',
    href: '/app/pipeline',
  },
  {
    title: 'Evaluation',
    body: 'JobEvaluator + LLMRouter: conviction score, H1B column, evidence JSON, calibration.',
    href: '/app/jobs',
  },
  {
    title: 'Tailor',
    body: 'TailorAgent: YAML + QA loop, manual JD tab, PDFs back to the sheet.',
    href: '/app/resume',
  },
  {
    title: 'Learning loop',
    body: 'Post-cycle hooks: digest, feedback ingest, filter learning, sourcing hints (CLI today).',
    href: '/app/settings',
  },
] as const;

export default function Overview() {
  return (
    <>
      <h1 className="app-page-title">Agent hub</h1>
      <p className="app-page-lead">
        This area is for the product that wires{' '}
        <strong>sourcing → JD verification → evaluation → tailoring → hooks</strong>, matching your
        pipeline in the repo. The UI will talk to{' '}
        <span className="app-code">apps/api</span> as endpoints land; the CLI remains the source of
        truth until then.
      </p>
      <div className="app-card-grid">
        {agents.map(({ title, body, href }) => (
          <Link
            key={title}
            to={href}
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <div className="app-card" style={{ height: '100%', cursor: 'pointer' }}>
              <h3>
                {title === 'Sourcing' && <Search size={18} />}
                {title === 'Evaluation' && <Scale size={18} />}
                {title === 'Tailor' && <FileEdit size={18} />}
                {title === 'Learning loop' && <BookOpen size={18} />}
                {title}
              </h3>
              <p>{body}</p>
            </div>
          </Link>
        ))}
      </div>
      <p className="app-muted" style={{ marginTop: '28px' }}>
        Run the full cycle locally:{' '}
        <span className="app-code">python3 apps/cli/run_pipeline.py</span> from the repository root
        (with <span className="app-code">config/</span> and env keys in place).
      </p>
    </>
  );
}
