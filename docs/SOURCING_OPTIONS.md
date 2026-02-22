# Sourcing options: more and better jobs

Ways to source more jobs, higher-quality or “better company” jobs, and APIs/MCPs you can plug in.

---

## 1. APIs already added in this project

| Source | Notes |
|--------|--------|
| **Remotive** | Free API, remote-only. Max ~4 requests/day; must credit Remotive. See `src/scrapers/remotive_scraper.py`. |
| **Remote OK** | Free JSON feed at `remoteok.com/api`. Remote jobs, no auth. See `src/scrapers/remoteok_scraper.py`. |
| **Ashby** | Public job board API; add company slugs (e.g. Notion, Figma, Linear, Vercel). See `src/scrapers/ashby_scraper.py`. |
| **ATS (Greenhouse / Lever)** | Board list is configurable via `config/pipeline.yaml` → `sourcing.ats_boards`. |

---

## 2. Other APIs worth adding

| API | Auth | Notes |
|-----|------|--------|
| **Adzuna** | Free key (developer.adzuna.com) | Search by keyword, location, salary. US + other countries. Good for volume. |
| **USAJobs.gov** | API key | US federal jobs. Useful if you target government. |
| **Otta** | Unknown | Curated tech/startup roles (UK/remote). Check otta.com for API. |
| **Unified.to** | Paid | Single API for 63+ ATS (Greenhouse, Lever, Workday, etc.). Reduces custom scrapers. |

---

## 3. “Better company” / quality ideas

- **Curated company list**  
  Maintain a list of target companies (e.g. YC, “target tier”) and tag or prioritize jobs from those companies in the sheet or in filters.

- **YC jobs**  
  Y Combinator job board (jobs.ycombinator.com) – many startups; scrape or use any official/community API.

- **Wellfound (AngelList)**  
  Startup jobs with company/funding context. Official API exists; third‑party scrapers (e.g. Apify) are paid.

- **Expand ATS boards**  
  Add more Greenhouse/Lever/Ashby boards from companies you care about. Use `config/pipeline.yaml` → `sourcing.ats_boards` so you don’t hardcode.

- **Levels.fyi / Blind**  
  Not job APIs; use for company/salary/level context when evaluating or ranking.

---

## 4. RSS / feeds

- **Indeed RSS**, **Stack Overflow Jobs RSS**, company career page RSS feeds.  
- Parse with `feedparser` and normalize to your job schema for one more pipeline input.

---

## 5. MCPs (Model Context Protocol)

- **Current MCPs in this repo**  
  `cursor-ide-browser` (navigate pages), `user-context7` (docs). No job-board MCP by default.

- **Custom job MCP**  
  Build an MCP server that:
  - Calls Adzuna, Remotive, Remote OK, etc.
  - Normalizes to a single “job” schema.
  - Exposes tools like `search_jobs(query, location, limit)` so an agent can pull jobs in a run.

- **Browser MCP**  
  Can automate visiting job boards; fragile and may violate ToS. Prefer APIs where possible.

---

## 6. Data quality

- **Dedupe**  
  Beyond URL: same company + title + location from two sources → treat as one (e.g. keep one, mark “also on X”).

- **Freshness**  
  Prefer “posted in last 24–48h” when the API supports it (e.g. JobSpy `hours_old`, Remotive `publication_date`).

- **Salary / level**  
  When available (Remotive, Remote OK, some ATS), store in the sheet and use in evaluation or ranking.

---

## 7. Config

- **Queries / locations**  
  `config/pipeline.yaml` → `sourcing.queries`, `sourcing.locations`.

- **ATS boards**  
  `config/pipeline.yaml` → `sourcing.ats_boards` (greenhouse, lever, ashby slugs). See `config/pipeline.yaml` and `src/scrapers/ats_scraper.py`.

- **Enable/disable sources**  
  You can add `sourcing.sources: [jobspy, community, jobright, remotive, remoteok, ats]` and have the pipeline only run selected sources.
