export default function Resume() {
  return (
    <>
      <h1 className="app-page-title">Resume & tailor</h1>
      <p className="app-page-lead">
        High-conviction pipeline tailoring and the <strong>Manual_JD_Tailor</strong> flow: JD fetch,
        TailorAgent QA loop, LaTeX/PDF paths on disk, sheet status columns. Canonical resume files live
        under <span className="app-code">core_agents/resume_agent/Resume_Building/Abhishek/</span> (see{' '}
        <span className="app-code">data/resumes/README.md</span> in the repo).
      </p>
      <div className="app-card">
        <h3>
          Tailor runs <span className="app-badge">Coming soon</span>
        </h3>
        <p className="app-muted" style={{ marginTop: '8px' }}>
          CLI today:{' '}
          <span className="app-code">python3 scripts/tools/tailor_from_urls.py --from-tailor-tab</span>. This
          page will list runs and artifacts when the API exposes them.
        </p>
      </div>
    </>
  );
}
