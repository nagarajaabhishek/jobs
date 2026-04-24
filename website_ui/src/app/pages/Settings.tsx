export default function Settings() {
  return (
    <>
      <h1 className="app-page-title">Settings & hooks</h1>
      <p className="app-page-lead">
        Mirrors <span className="app-code">config/pipeline.yaml</span> and cycle hooks: digest, feedback
        ingest, filter learning, sourcing hints, career strategy. Sensitive values stay in{' '}
        <span className="app-code">.env</span>.
      </p>
      <div className="app-card">
        <h3>
          Remote config <span className="app-badge">Coming soon</span>
        </h3>
        <p className="app-muted" style={{ marginTop: '8px' }}>
          Edit YAML safely from this screen once authenticated APIs exist; until then manage files in the
          repo.
        </p>
      </div>
    </>
  );
}
