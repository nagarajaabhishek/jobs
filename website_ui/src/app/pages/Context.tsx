export default function Context() {
  return (
    <>
      <h1 className="app-page-title">Profile context</h1>
      <p className="app-page-lead">
        <span className="app-code">master_context.yaml</span> and compiled{' '}
        <span className="app-code">dense_master_matrix.json</span> are required before evaluation (product
        contract). Future: guided edits and rebuild without only using the CLI.
      </p>
      <div className="app-card">
        <h3>
          Context editor <span className="app-badge">Coming soon</span>
        </h3>
        <p className="app-muted" style={{ marginTop: '8px' }}>
          Rebuild matrix locally:{' '}
          <span className="app-code">python3 apps/cli/scripts/tools/build_dense_matrix.py</span>
        </p>
      </div>
    </>
  );
}
