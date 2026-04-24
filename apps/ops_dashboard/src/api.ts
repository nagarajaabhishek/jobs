/**
 * All requests use relative /api so Vite dev proxy forwards to FastAPI (:8000).
 */

export type JobRow = {
  row_index: number;
  status: string;
  role_title: string;
  company: string;
  location: string;
  job_link: string;
  source: string;
  apply_score: number | null;
  match_type: string;
  recommended_resume: string;
  h1b_sponsorship: string;
  resume_status: string;
  resume_path: string;
  apply_bucket: string;
  reasoning_preview: string;
};

export type JobsResponse = {
  tab: string;
  count: number;
  jobs: JobRow[];
};

export async function fetchJobs(params: Record<string, string | number | boolean>): Promise<JobsResponse> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    q.set(k, String(v));
  }
  const r = await fetch(`/api/v1/jobs?${q.toString()}`);
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  return r.json();
}

export async function fetchJobDetail(url: string): Promise<{ tab: string; job: Record<string, string | number> }> {
  const r = await fetch(`/api/v1/jobs/detail?${new URLSearchParams({ url })}`);
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  return r.json();
}

export async function fetchSheetMeta(): Promise<{
  worksheet_tab: string;
  spreadsheet_id_preview: string;
  project_root: string;
}> {
  const r = await fetch('/api/v1/meta/sheet');
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  return r.json();
}

export function resumeFileUrl(resumePath: string): string {
  return `/api/v1/files/resume?${new URLSearchParams({ path: resumePath })}`;
}
