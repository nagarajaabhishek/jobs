# Research Deep Dive: Phase 1 - Alumni-Sourced Prioritization

## 1. The Core Problem: The "Cold Sourcing" Trap
Currently, platforms like LinkedIn, Indeed, and even aggregator-based AI tools (like JobRight.ai) use **Cold Sourcing**. They scrape the internet for every available job posting and dump them into a massive feed.

**The resulting drawbacks for the student are severe:**
- **The "Ghost Job" Phenomenon:** Over 40% of jobs listed on major boards are either already filled, permanently open just to collect resumes, or simply don't exist.
- **The Black Hole:** A student applying "cold" to a Fortune 500 company on LinkedIn is competing against 5,000+ other random applicants. The signal-to-noise ratio is zero.
- **Search Fatigue:** Students spend 80% of their time scrolling and filtering identical feeds across 4 different platforms instead of tailoring applications.

## 2. The Solution: "Warm Sourcing" via Alumni Data
The highest signal indicator of a company’s willingness to hire a student from a specific university (e.g., UTA) is **historical hiring data**. If a company hired 10 UTA alumni last year, they have an established pipeline, familiarity with the curriculum, and trust in the university's output. 

**The Hypothesis:** Applications routed to "Warm" companies will yield a statistically significant higher interview rate than cold applications, even if the student's raw credentials are identical.

## 3. Data Acquisition Strategy (How to get the "Warm" List)
To execute this, the app requires a robust dataset mapping Alumni to Employers. This can be built in stages:

### Tier 1: Public OSINT (Open Source Intelligence)
- **LinkedIn Alumni Tool Scraping:** Automating a search on LinkedIn for "[University Name] Alumni" and aggregating the "Where they work" metric. 
- **Advantage:** Free, requires no university permission.
- **Disadvantage:** LinkedIn actively blocks scrapers; data can be noisy (e.g., "Self-Employed" or generic tech giants masking real trends).

### Tier 2: B2B University Partnerships (The Real Moat)
- **First Destination Surveys (FDS):** Every university collects FDS data for accreditation (where graduates get their first job). The app ingests this proprietary dataset from the Career Center.
- **Advantage:** 100% verified data, highly specific to recent grads (the exact target demographic), completely inaccessible to B2C competitors like JobRight.

### Tier 3: The "Shadow Market" (Direct Employer Portals)
- Many regional employers don't want to pay LinkedIn massive fees to post junior roles. They prefer to post directly on their own ATS (Greenhouse, Workday) and notify local universities.
- **Advantage:** These jobs have virtually zero "Cold" applicants because they are so hard to find organically.

## 4. Technical Architecture: Reversing the Sourcing Funnel
Instead of running a giant scraper that looks for *jobs* and tries to match them to *students*, we invert the logic.

**Current Sourcing (The JobRight Model):**
1. Scrape millions of jobs.
2. Filter by keyword.
3. Show student.

**Alumni-Sourced Prioritization (Your Model):**
1. **Generate Target List:** Script queries the University Alumni Database (or LinkedIn scrape) and generates a tightly curated list of 200 "High-Probability Employers" for a specific major (e.g., Data Science at UTA).
2. **Targeted ATS Scraping:** The `sourcing_agent.py` script *only* monitors the direct career pages (Greenhouse, Lever, Workday) of those 200 specific companies.
3. **The "Warm" Feed:** The student is presented with a highly curated feed: *"Here are 4 open roles at companies that hired 12 of your classmates last year."*

## 5. Strategic Advantages & The Competitive Moat

1. **Massive Reduction in Compute Costs:** By scraping via a targeted list of 200 URLs instead of attempting to parse 50,000 LinkedIn postings daily, your infrastructure costs drop to near zero while maintaining much higher quality.
2. **Trust & Authenticity:** When a student sees exactly *why* a job is recommended (e.g., "UTA Alumni work here"), their trust in the platform skyrockets compared to a generic "AI 95% Match" score.
3. **The Network Effect Flywheel:** 
   - You prove high ROI to University A.
   - University A gives you better integration with their internal employer network.
   - Your job feed gets even more exclusive.
   - University B buys the software because they want the same exclusive employer insights.

## Next Steps for Validation (MVP Development)
We can test this immediately in the `Job_Automation` codebase.
1. Create a `target_companies.json` file containing a manually compiled list of 15 companies known to hire from your university.
2. Write a Python script (`alumni_scraper.py`) that specifically targets the career pages of those 15 companies.
3. Compare the quality of those fetched jobs against a generic LinkedIn search.
