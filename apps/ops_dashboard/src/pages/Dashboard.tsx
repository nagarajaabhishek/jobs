import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchJobs, fetchSheetMeta, resumeFileUrl, type JobRow } from '../api';

export default function Dashboard() {
  const [meta, setMeta] = useState<{ worksheet_tab: string; spreadsheet_id_preview: string } | null>(null);
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [tab, setTab] = useState('');
  const [minScore, setMinScore] = useState(70);
  const [topOnly, setTopOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSheetMeta()
      .then((m) => {
        setMeta({ worksheet_tab: m.worksheet_tab, spreadsheet_id_preview: m.spreadsheet_id_preview });
        setTab((prev) => prev || m.worksheet_tab);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!tab) return;
    const t = tab;
    setLoading(true);
    setError(null);
    fetchJobs({
      tab: t,
      min_score: minScore,
      limit: 150,
      must_apply_only: topOnly,
    })
      .then((r) => setJobs(r.jobs))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tab, minScore, topOnly]);

  return (
    <>
      <h2>Apply queue</h2>
      <p className="lead">
        Jobs from your Google Sheet daily tab: scores, match tier, recommended resume variant, H1B signal,
        and links to tailored files when present. Backend: same credentials as the CLI (
        <code>config/credentials.json</code>).
      </p>

      {meta && (
        <p className="meta">
          Sheet tab: <strong>{tab || meta.worksheet_tab}</strong>
          {meta.spreadsheet_id_preview ? ` · Spreadsheet: ${meta.spreadsheet_id_preview}` : null}
        </p>
      )}

      <div className="filters">
        <label>
          Tab (YYYY-MM-DD){' '}
          <input value={tab} onChange={(e) => setTab(e.target.value)} placeholder="e.g. 2026-04-15" />
        </label>
        <label>
          Min score{' '}
          <input
            type="number"
            min={0}
            max={100}
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
          />
        </label>
        <label>
          <input type="checkbox" checked={topOnly} onChange={(e) => setTopOnly(e.target.checked)} /> Must-apply /
          Strong only
        </label>
        <button type="button" className="btn" onClick={() => setTab(meta?.worksheet_tab || '')}>
          Reset tab to config default
        </button>
      </div>

      {error && <div className="card err">{error}</div>}
      {loading && !error && <p className="muted">Loading…</p>}

      {!loading && !error && (
        <div style={{ overflowX: 'auto' }}>
          <table className="data">
            <thead>
              <tr>
                <th>Score</th>
                <th>Match</th>
                <th>Role</th>
                <th>Company</th>
                <th>H1B</th>
                <th>Recommended resume</th>
                <th>Resume</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.row_index + j.job_link}>
                  <td className="score">{j.apply_score ?? '—'}</td>
                  <td>{j.match_type || '—'}</td>
                  <td>{j.role_title}</td>
                  <td>{j.company}</td>
                  <td>{j.h1b_sponsorship || '—'}</td>
                  <td>{j.recommended_resume || '—'}</td>
                  <td>
                    {j.resume_path ? (
                      <a href={resumeFileUrl(j.resume_path)} target="_blank" rel="noreferrer">
                        Open file
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>
                    <Link to={`/job?url=${encodeURIComponent(j.job_link)}`}>Details</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {jobs.length === 0 && <p className="lead">No rows match filters.</p>}
        </div>
      )}
    </>
  );
}
