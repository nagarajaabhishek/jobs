export default function Pipeline() {
  return (
    <>
      <h1 className="app-page-title">Pipeline</h1>
      <p className="app-page-lead">
        Orchestrates preflight, sourcing batches, evaluation sweeps, phase gates, and cycle hooks (
        <span className="app-code">run_pipeline.py</span>
        ). Here you will trigger runs, see cycle ID, and tail status once the API streams logs or job
        summaries.
      </p>
      <div className="app-card">
        <h3>
          Status <span className="app-badge">Coming soon</span>
        </h3>
        <p className="app-muted" style={{ marginTop: '8px' }}>
          Connect to <span className="app-code">GET /v1/pipeline/status</span> (to be implemented) or
          webhook payloads from your runner.
        </p>
      </div>
    </>
  );
}
