import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchJobDetail, resumeFileUrl } from '../api';

export default function JobDetail() {
  const [params] = useSearchParams();
  const url = params.get('url') || '';
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<Record<string, string | number> | null>(null);
  const [tab, setTab] = useState('');

  useEffect(() => {
    if (!url) {
      setError('Missing url query parameter.');
      return;
    }
    setError(null);
    fetchJobDetail(url)
      .then((r) => {
        setTab(r.tab);
        setJob(r.job as Record<string, string | number>);
      })
      .catch((e) => setError(String(e)));
  }, [url]);

  const evidenceRaw = job ? String(job['Evidence JSON'] ?? '') : '';
  const evidencePretty = useMemo(() => {
    if (!evidenceRaw.trim()) return '';
    try {
      return JSON.stringify(JSON.parse(evidenceRaw), null, 2);
    } catch {
      return evidenceRaw;
    }
  }, [evidenceRaw]);

  if (!url) {
    return (
      <>
        <h2>Job detail</h2>
        <p className="err">Open a job from the dashboard.</p>
        <Link to="/">← Dashboard</Link>
      </>
    );
  }

  return (
    <>
      <p className="meta">
        <Link to="/">← Dashboard</Link>
        {tab ? ` · Tab ${tab}` : null}
      </p>
      <h2>Job detail</h2>
      {error && <div className="card err">{error}</div>}
      {job && (
        <>
          <div className="card">
            <strong>{String(job['Role Title'] || '')}</strong> · {String(job['Company'] || '')}
            <div className="lead" style={{ marginTop: 12 }}>
              Apply score: <span className="score">{String(job['Apply Score'] ?? '—')}</span> ·{' '}
              {String(job['Match Type'] || '')}
            </div>
            <p>
              <a href={String(job['Job Link'] || '')} target="_blank" rel="noreferrer">
                Job posting
              </a>
            </p>
            <p>
              <strong>Recommended resume:</strong> {String(job['Recommended Resume'] || '—')}
            </p>
            <p>
              <strong>H1B:</strong> {String(job['H1B Sponsorship'] || '—')}
            </p>
            <p>
              <strong>Resume status:</strong> {String(job['Resume Status'] || '—')}
            </p>
            {String(job['Resume Path'] || '').trim() ? (
              <p className="row-actions">
                <a
                  href={resumeFileUrl(String(job['Resume Path']))}
                  target="_blank"
                  rel="noreferrer"
                  className="btn"
                  style={{ textDecoration: 'none' }}
                >
                  Open tailored file (PDF/TEX)
                </a>
              </p>
            ) : null}
          </div>
          <h3 style={{ fontSize: '1rem', marginTop: 24 }}>Reasoning</h3>
          <div className="card" style={{ whiteSpace: 'pre-wrap' }}>
            {String(job['Reasoning'] || '—')}
          </div>
          {evidencePretty && (
            <>
              <h3 style={{ fontSize: '1rem', marginTop: 24 }}>Evidence JSON</h3>
              <pre className="json">{evidencePretty}</pre>
            </>
          )}
        </>
      )}
    </>
  );
}
