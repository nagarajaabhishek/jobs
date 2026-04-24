export default function Jobs() {
  return (
    <>
      <h1 className="app-page-title">Jobs & evaluation</h1>
      <p className="app-page-lead">
        Surface rows from Google Sheets (or a future store): NEW / EVALUATED / NEEDS_REVIEW, Apply
        Score, Evidence JSON, H1B sponsorship, skill gaps. Backed by{' '}
        <span className="app-code">JobEvaluator</span> today.
      </p>
      <div className="app-card">
        <h3>
          Job feed <span className="app-badge">Coming soon</span>
        </h3>
        <p className="app-muted" style={{ marginTop: '8px' }}>
          Planned: <span className="app-code">GET /v1/jobs</span> with filters. Until then, use the Daily
          Jobs tab in Sheets as the live view.
        </p>
      </div>
    </>
  );
}
