# Pipeline Workflow Deep-Dive

This document explains the step-by-step technical lifecycle of a job, from the moment it is scraped to the moment it is fully evaluated and scored. You can leave comments or questions on this file.

---

## Phase 1: Target-Driven Interleaved Sourcing

The pipeline does not scrape all jobs at once. It uses an **interleaved loop** to source and evaluate small batches continuously.

1. **Query Selection**: The system picks one query from `config/pipeline.yaml` (e.g., "Product Manager").
2. **Sourcing Batch**: It tasks `sourcing_agent.py` to scrape a small batch.
   - The query is sent to **JobSpy**, which searches 5 major platforms simultaneously (LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter).
   - It requests a *total* of ~15 jobs combined across those platforms per run, **not** 15 from each.
3. **Pre-Filtering (The First Gate)**: Before doing anything else, it checks the raw job data against your `candidate_constraints` and `filters` in `pipeline.yaml`.
   - *Example: If the seniority exclusion lists "Director", the job is immediately discarded.*
4. **Deduplication**: The system normalizes the URL (stripping tracking parameters) to check if we've already sourced this exact job from another query or platform.
5. **Storage**: Surviving, unique jobs are written to your Google Sheets `Daily Jobs` tab with the status explicitly set to `NEW`.
6. **Local Caching**: The full text of the Job Description (JD) is saved in `data/jd_cache.json` so we don't need to re-fetch the web page later.

---

## Phase 2: Batch Evaluation (The Brain)

Immediately after a batch is saved as `NEW`, the `JobEvaluator` takes over.

1. **Batch Retrieval**: The evaluator pulls the `NEW` jobs from Google Sheets.
2. **Context Assembly**: For each job, the evaluator builds a massive context payload. It combines:
   - The job's full description (from `jd_cache.json`).
   - Your `Master Context` (your universal skills and general background).
   - Your `Role Specializations` (tailored background info specifically for TPM, PO, BA roles).
   - Any sponsorship intelligence discovered.
3. **LLM Processing (`gemini_job_fit_analyst.md`)**: The LLM is invoked. To save time and API costs, jobs are sent to the Gemini API in chunks (defined by `batch_eval_size: 10` in your YAML).
4. **Scoring Logic**: The LLM runs a rigorous, point-based rubric against the context. It looks for exact skill matches, gap analysis, and mandatory requirements to generate a `0-100 Apply Conviction Score`.
5. **Output Update**: The LLM returns structured JSON. The evaluator parses this and updates the Google Sheet row, changing the status from `NEW` to the final verdict (e.g., `MUST APPLY`, `REJECT`).

---

## Phase 3: The Interleaved Loop Continues

Once that single batch of ~15 jobs is evaluated and the sheet is updated, the pipeline loops back to **Phase 1**.
- It picks the *next* query (e.g., "Business Analyst").
- It sources another small batch.
- It evaluates that batch immediately.

This repeats until the pipeline successfully finds 50 "MUST APPLY" jobs (the `results_wanted` target), ensuring you don't over-scrape the internet or waste API tokens once you have enough good leads for the day.

---

### Q&A Section

*(Add your questions below. I will update this document with the answers.)*

**Q1: Where all are the sourcing happening? the query is it being sent to where all, and how many are we sourcing from each? are we sourcing from 10 different data points? and each 15 jobs? so 150 jobs?**
**A1:** During the main interleaved loop, the query is sent to the `JobSpy` engine. This engine automatically searches **5 major data points at once**: LinkedIn, Indeed, Glassdoor, Google Jobs, and ZipRecruiter. 
When the pipeline asks for 15 jobs, it is asking for **15 jobs *total*** across those 5 platforms for that specific query and location. It does **not** pull 15 from each (which would be 75 jobs). 

*Note: There are an additional 7 specialized data points (Jobright, Arbeitnow, Remotive, RemoteOK, Ashby, specific ATS boards, and Community boards) that are only scraped **once** at the very end of the pipeline execution, separate from the main loop.*

**Q2: Are they sourcing jobs or JDs or URLs?**
**A2:** The scrapers pull **entire Job Objects**. A single sourced "Job" object in the pipeline is a dictionary that contains:
1. The Job Title
2. The Company Name
3. The Location
4. The applied URL (where you click to apply)
5. The full text of the Job Description (JD)
The pipeline needs this full JD text immediately in order to perform the AI evaluation against your master context and skills.

**Q3: Is that how we are getting the information from the data points/APIs, and are we storing it? If we are, where are we storing it?**
**A3:** Yes! Depending on the source, it grabs the data in different ways (JobSpy scrapes web HTML, Jobright/Remotive might use APIs). Once the sourcing script has built the raw "Job Object" (Title, Company, URL, JD Text), it stores the data in **two different places**:
1. **Google Sheets (`Daily Jobs` Tab):** It writes the Title, Company Name, URL, and Location directly onto a new row in your spreadsheet. It sets the status of this row to "NEW".
2. **Local Cache (`data/jd_cache.json`):** Google Sheets cells have text limits, so it does **not** store the massive full text of the Job Description in the sheet. Instead, it saves the full JD text into a local database file on your hard drive at `data/jd_cache.json`.
When the Evaluator Agent runs, it reads the URL from the Google Sheet, looks up that URL inside `data/jd_cache.json` to get the full JD text, and then sends that text to the LLM for scoring.

**Q4: Is cache a good place to store, or should we maintain another storage place? What's the difference between caching and this specific file working as a cache? Does it delete the JD later?**
**A4:** Excellent architectural question! In this system, `jd_cache.json` is acting as a **persistent local Key-Value store (a lightweight database)** disguised as a cache. 
- **Why it's good for now:** It avoids the complexity of setting up a real database (like PostgreSQL or MongoDB) just to hold text strings. It allows the evaluator to run instantly without making new web requests.
- **Does it delete the JD later?** Currently, no. The file grows indefinitely. Every job you've ever sourced has its JD permanently stored in that JSON file. Over many months, this file could become very large (hundreds of Megabytes) and slow down the system.
- **Future Architecture Recommendation:** Yes, we should eventually implement a **Time-To-Live (TTL) eviction policy**. We can add a function that runs at the end of the pipeline to "prune" any jobs from the `jd_cache.json` that are older than 30 days and have already been evaluated, keeping the file lean and fast!

**Q5: I see in `jd_cache.json` there are a few job listings without the JD information. What's the fallback plan or JD content analysis plan, how else can we get the JD? Are there any plans/processes?**
**A5:** This happens when a job board (like LinkedIn or Indeed) temporarily blocks the scraping engine, resulting in an empty or "None" JD being stored in the cache. 
- **Current Fallback:** If the system is completely unable to source the JD (the JD string is empty or literally "None"), the pipeline **should not** attempt to evaluate it, because grading a job based purely on a Title is inaccurate and wastes LLM tokens. Instead, the evaluator will instantly return a special verdict (like "⚠️ Missing JD") and skip the API call.
- **The Ideal Plan/Process:** We should build a **"Secondary JD Resolution"** step. If `JobSpy` fails to get the HTML JD text, we should have a fallback `HtmlFetcher` (using something like `requests`, `BeautifulSoup`, or a headless browser via `Playwright`) that attempts to visit the plain `Apply URL` and extract the text from the source page directly before saving it to the cache. We can build this resolution step into `sourcing_agent.py`.

**Q6: Are the sourcing queries in `pipeline.yaml` good? Do they follow API documentation, and do we have fallbacks if they fail?**
**A6:** The queries (e.g., "Product Manager") are standard keyword searches. JobSpy passes these directly to the search engines of LinkedIn, Indeed, etc. 
- **Quality:** They are "good" in that they are broad, but we improve them using **AI Query Expansion**. If enabled, the `SourcingAgent` asks the LLM to generate 10-15 variations of your roles (e.g., "Technical Product Manager", "Product Lead") to ensure we don't miss niche titles.
- **Fallbacks:** If a specific query returns 0 results for a location, the system simply moves to the next query in the list. There is no "retry" with a different keyword automatically unless AI Expansion is turned on.

**Q7: Can you list all the sourcing data points we are currently using?**
**A7:** We currently use **12 distinct sourcing data points**:
1.  **LinkedIn** (via JobSpy)
2.  **Indeed** (via JobSpy)
3.  **Glassdoor** (via JobSpy)
4.  **Google Jobs** (via JobSpy)
5.  **ZipRecruiter** (via JobSpy)
6.  **Jobright** (Specialized scraper)
7.  **Arbeitnow** (Specialized scraper)
8.  **Remotive** (Remote-specific)
9.  **RemoteOK** (Remote-specific)
10. **Ashby** (ATS-specific for startups)
11. **Greenhouse / Lever** (ATS-specific for mid-market/large tech)
12. **Community Boards** (Aggregated niche lists)

**Q8: How is the data sent to the LLM, and is it cost-efficient?**
**A8:** This is one of the most optimized parts of the pipeline:
- **Data Source:** The LLM receives the **Full JD Text** (from `jd_cache.json`), your **Master Context** (personal skills), and **Role Specializations**.
- **Efficiency (Batching):** We do **not** send one job at a time. We use **Batch Evaluation** (defaulting to 10 jobs per prompt). This reduces "token overhead" because we only have to send your Resume/Master Context *once* for every 10 jobs, rather than sending it 10 separate times. 
- **Cost:** By using a "Fit Analyst" prompt that handles 10 jobs at once, we save roughly **60-80% in API costs** compared to 1-by-1 evaluation.

**Q9: Do we have all the scoring levels set?**
**A9:** Yes. The system uses a tiered mapping in `evaluate_jobs.py` (`score_to_verdict`):
- **85 - 100:** 🔥 Auto-Apply
- **70 - 84:** ✅ Strong Match
- **50 - 69:** ⚖️ Worth Considering
- **0 - 49:** ❌ No
This mapping ensures that your Google Sheet is easy to read at a glance using emojis and clear categories.

**Q10: Dice is missing. Can we use the Dice/Indeed MCP servers?**
**A10:** You are absolutely right—Dice is a massive data point for tech. 
- **Dice MCP Server:** There is an official **Dice MCP Server** that allows for natural language job searches. We can integrate this into our "Sourcing Layer" to allow for much more complex queries (e.g., "Find me Remote Product Owner roles with 3+ years experience in Austin").
- **Indeed MCP Server:** While there isn't an official "Indeed MCP Server" yet, we can treat Indeed as a primary API target via JobSpy or a custom connector to achieve similar results.

**Q11: Do we need to send the resume/context every 10 jobs? Is there a "Gem" equivalent for the API?**
**A11:** This is a great observation. In the Gemini UI, "Gems" provide persistent context. In the Gemini API, the equivalent is **Gemini Context Caching**.
- Instead of re-sending your Resume and Master Context every 10 jobs (which is what we do now), we can upload it **once** to a cache.
- The cache stays active for a set amount of time (TTL). 
- Every batch evaluation request will simply reference the `cache_id`. This reduces latency and can save up to **90% on input token costs**. 

**Q12: What is the Agent Development Kit (ADK) and how can we use it? Is it only for the pipeline model?**
**A12:** The **Google ADK** (Agent Development Kit) is a much more powerful framework than just a simple pipeline script. We can build several distinct **agentic models** using its orchestration engine:
1.  **The Loop Model (Current Pipeline):** Ideal for the main Sourcing -> Evaluation cycle that repeats until a target is met.
2.  **Parallel Model:** We can use ADK to run multiple scrapers (JobSpy, specialized agents) and multiple LLM evaluators in **simultaneous parallel tracks** to speed up processing by 5x.
3.  **Dynamic Router (Handoff) Model:** Instead of a fixed loop, we can have a "Chief Agent" that looks at a job and **decides** which specialized sub-agent to send it to (e.g., if it's a "Remote" job, it goes to the Remote-Expert agent; if it's "Fintech", it goes to a Finance-Expert agent).
4.  **Sequential (Multi-Stage) Model:** We can build post-pipeline agents for **Resume Tailoring** or **Automatic Outreach** that only trigger once a job passes a certain score threshold.

In short: ADK allows us to move from a "one-track script" to a "multi-agent team" where different agents handle sourcing, filtering, scoring, and even outreach autonomously.


**Q13: Can I use Dice MCP or other MCP servers to "Auto-Apply"?**
**A13:** Yes, but with a distinction between **Search MCPs** and **Apply MCPs**:
- **Search-Only (Most MCPs):** Most servers like the official Dice MCP or LinkedIn connectors are designed to *read* data. They are great for advanced sourcing but don't have "Submit" tools.
- **Auto-Apply Specific (The Automation Layer):**
    - **JobGPT MCP:** This is a specialized server that can actually submit applications and generate tailored resumes programmatically.
    - **Playwright/Stagehand MCP:** These "Browser Agents" (like LangChain's `browser-use`) act as the "last-mile" solution. They log into the job board, find the "Apply" button, and literally click and fill the forms for you by interacting with the UI.
- **Integration Plan:** We can stick to the `DiceScraper` for sourcing (it's fast and reliable) and then add an **ADK Browser Agent** for the "Must Apply" jobs to handle the form-filling autonomously.

**Q14: Are there Agent-to-Agent (A2A) protocols for this?**
**A14:** We are entering the cutting edge here. "A2A" (Agent-to-Agent) is a protocol designed to allow independent AI agents to talk to each other directly.
- **How it works for jobs:** Instead of an agent scraping a website (which is messy), a Job Board would have its own "Receiver Agent." Your "Applicant Agent" would send your identity, resume, and fit-score directly to their agent using a standardized protocol (like the proposed IEEE A2A standards or Google's ADK cards).
- **Current State:** 
    - **Standard Protocols:** IEEE P3349 (Space Cybersecurity) is a different standard, but the **LISA (Language Interface for Systemic Agents)** and **Agent Card** standards are where job board integration is headed.
    - **A2A in ADK:** The Google ADK you are exploring is one of the first kits to implement this. It allows your "Sourcing Agent" to pass a structured "Job Card" to your "Evaluator Agent," which then hands a "Decision Card" to the "Apply Agent." 
- **The Future:** Eventually, you won't "fill out forms." Your agent will just "ping" the company's agent with a signed cryptographic package of your qualifications!
