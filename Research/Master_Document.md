# Master Document: Job Sourcing & Evaluation Application

## 1. Competitive Analysis: Handshake
Handshake is the primary incumbent in the university space. While they have historically been a simple job board, they are aggressively moving into AI.

**Does Handshake do AI Evaluation?** Yes. Handshake has recently rolled out several AI-powered features specifically for employers and students:
- **AI Applicant Ranking (Pro Feature):** Employers can set "Candidate Criteria" (e.g., "Internship at a Big 4 firm"). Their AI then ranks applicants from "Recommended" down to least matched.
- **AI-Powered Matches:** Candidates are sorted by a "Best Match" algorithm on the employer's dashboard based on qualifications and engagement.
- **AI Summaries:** For recommended applicants, Handshake generates a short summary explaining why they are a strong match based on their profile data.

**Major Strategic Drawbacks for Handshake:**
- **Employer-Centric Bias:** Their AI evaluation is built to help employers filter students out, not to help students improve. This creates a "black box" for the student.
- **Conservative Logic:** Because they are an institutional partner, their AI is often just a sophisticated keyword filter rather than a true evaluator.
- **Institutional Lock-in (The UTD Example):** Universities like UT Dallas (UTD) use Handshake as their exclusive, mandatory platform for all on-campus and off-campus student employment. Because UTD forces adoption, Handshake has little incentive to innovate on *student success*, only on *employer volume*.

## 2. Inaccuracy Feedback: JobRight & LinkedIn
Users frequently report that AI analysis on these platforms feels "confidently wrong."

**LinkedIn Accuracy Issues (User Feedback):**
- **The "Top Applicant" Lie:** Many Premium users report being labeled as a "Top Applicant" for jobs where they meet zero requirements.
- **Domain Blindness:** LinkedIn’s AI fails to distinguish between vastly different seniority levels.
- **Taxonomy Failure:** It struggles with non-standard job titles (e.g., mapping "Ninja" to "Developer").

**JobRight: JD-Rewriting vs. Real Context:**
- **Current Logic:** JobRight primarily performs Keyword Mapping. It takes your base resume and "optimizes" it for a specific Job Description (JD).
- **The "Hallucination" Risk:** Because it prioritizes "passing the ATS," it often over-inflates or "fakes" data to match the JD requirements.
- **Formatting "Bloat":** The AI is often "too wordy," ignoring the standard 1-page rule for students.

## 3. B2B Strategy: Selling to Universities
Universities (like UTA) don't buy job boards; they buy Career Outcomes and Student Retention.

**The "Gap" Your Application Fills:**
- Handshake tells them *who* got hired.
- Your App tells them *why* the others didn't and *how* to fix the curriculum.

**High-Value B2B Features (The "Buy" Signal):**
- **Curriculum Alignment Analytics:** Provide a dashboard to Department Heads showing: "60% of our Engineering Management students are failing the 'Agile' match for DFW jobs. We should add a Scrum certification module to Course X."
- **Career Readiness Score (The "FICO" for Jobs):** A metric universities can use to identify "at-risk" students who are graduating soon but have low evaluation scores.
- **Alumni Benchmarking:** Compare current student resumes against successful Alumni from the same program.
- **Accreditation Data:** Generate reports for "ABET" or "AACSB" accreditation on student "skill mastery" based on job evaluation data.

**The Land-and-Expand Strategy:**
- **Step 1:** Prove out the B2B model locally with a pilot at **UTA** (University of Texas at Arlington).
- **Step 2:** Expand to **UTD** (University of Texas at Dallas). UTD is a major engineering and business hub in the DFW metroplex that currently relies heavily on Handshake. By proving our Curriculum ROI vs. Handshake's volume metrics, UTD is the perfect expansion target.
- **Step 3:** Expand across the broader UT System and state university networks.

## 3.1. Our Central Unique Selling Proposition (USP)
To succeed, our application provides dual-sided, complementary value that no incumbent currently offers:

**1. The USP for Students: Frictionless, Centralized Pipeline**
Students are exhausted by checking 5 different job boards every day and guessing which resume to submit. Our USP solves BOTH problems:
- **Centralized Daily Feed:** Students stop hunting across platforms. They open our app and see a curated feed of the top 100 jobs for the day, centrally located in one place.
- **Pre-Evaluated Fit:** Because our automated backend (`evaluate_jobs.py` + `llm_router.py`) asynchronously maps these jobs against *all* of the student's internal profiles (e.g., TPM, Analyst, GTM), the student knows immediately if they are a fit, *and exactly which resume to use*, before they even click "Apply." Zero copy-pasting or guessing required.
- **The Alumni Advantage (Warm Sourcing):** The feed isn't just random jobs. We specifically scrape and prioritize roles from companies with a proven track record of hiring alumni from exactly their university and program. This turns "cold applications" into "warm introductions."

**2. The USP for Universities: Closing the Curriculum Data Loop**
Universities currently fly blind after graduation. Handshake tells them *who* got hired. Our USP tells the department head exactly *why* their students are failing (e.g., 60% of applicants lacked SQL) and provides actionable intelligence on exactly what syllabus changes are needed to fix it, proving the financial ROI of the degree.

## 4. Feature: The "Prescriptive Gap Analysis"
This feature helps students understand what they lack and helps professors update their syllabi to increase enrollment.

**Student-Facing: "The Career Roadmap"**
- **Gap Identification:** Instead of just a "match score," the app provides a Gap List (e.g., "You lack experience with JIRA and Tableau").
- **Prescriptive Learning:** The app suggests specific University courses (e.g., "Enroll in IE 5301 to gain these missing skills") or external certifications.
- **Outcome Projection:** "Taking this 1-credit elective will increase your match score for 'Project Manager' roles by 15%."

**Professor-Facing: "The Enrollment Driver"**
- **Syllabus Optimization:** Professors receive an automated report of the top 5 trending skills in their field's job descriptions.
- **Enrollment Strategy:** By adding a "trending skill" (e.g., "AI-Powered Logistics") to a course description, professors can prove the ROI of their class, leading to higher student demand and enrollment.

## 5. Drawbacks & Competitive Moat Analysis
**Major Drawbacks (The "Moat"):**
- **The University Data Loop:** Handshake and JobRight cannot easily access internal university course descriptions, project rubrics, or student transcripts.
- **Authenticity vs. Automation:** JobRight is built for Volume. If your app is built for Authenticity (verifying skills through course projects), recruiters will prioritize your applicants.

## 6. Master Competitive Analysis Matrix

This consolidated matrix evaluates the current ecosystem based on user intent, matching mechanics, and critical structural drawbacks reported by actual candidates and recruiters.

| Platform | Primary User / Strategy | Matching Mechanism | Inaccuracy & Trust Deficits | The Value "Gap" |
|---|---|---|---|---|
| **Handshake** | **Employers** (Filtering and volume application). Requires manual static profile building. | "Best Match" algorithm based on basic qualifications and keywords logic set by employers. | **Institutional Inertia (The UTD Case Study):** Built to serve employers, not help students improve. Because Handshake holds the exclusive monopoly at universities like UT Dallas (UTD) for all student employment, they have zero incentive to innovate on *student success*. | No prescriptive gap analysis. Values access over improvement. |
| **Homegrown University Portals** | **Universities & Local Employers** (Custom data hookups directly to LMS). | Varies, usually simple title/keyword tagging or manual board parsing. | **The Resource/Utilization Trap:** Outdated, clunky UI leads to low student engagement ("empty rooms"). Plus, a recruiter doesn't want to create 50 different logins for 50 different university portals. | Offers deep student data control, but zero cross-university automation or real-time curriculum optimization. |
| **JobRight.ai** | **Students** (Speed and automated rewriting). Generates custom JD-driven resumes. | AI-Agent scanning the JD vs. Resume and extracting keywords. | **The Trust Deficit:** High hallucination risk. Fills out applications with fake evidence; generates bloat/spam that recruiters ignore. | Basic keyword scoring with zero academic context. |
| **Simplify** | **Students** (Form-filling automation). Basic profile used for auto-filling apps. | Keyword overlap and basic profile mapping. | **Shallow Context:** Autofill errors (visa/graduation). Treats a "Hello World" Python script the same as a Python thesis. Match score ignored. | Excellent for autofill extension, zero value for career tracking. |
| **LinkedIn** | **Professionals** (Networking). Skill tags with manual profile curation. | Skill tags combined with Premium 'Top Applicant' percentile logic. | **Domain Blindness:** Premium marketing tells users they are "Top 10%" for roles where they meet 0% of deep domain requirements. | Networking capabilities, but no true skill verification. |
| **Indeed/Glassdoor** | **Mass Market** (Sourcing). Basic parsing. | 'Smart Match' based primarily on Job Title and broad employer weights. | **Low Signal / High Noise:** High volume of generic suggestions and "Ghost Jobs" based on simple title parsing rather than culture fit. | None. |
| **Your App** | **Students & Universities** (Curriculum ROI). | **Verification-Based Matching.** Contextual mapping of the JD to graded university syllabi against multiple internal resumes via a background LLM. | **The Authenticity Moat:** Eliminates hallucinations because skills are strictly gated by verified academic projects and transcripts. | **Deep Prescriptive Gap Analysis.** Tells the student exactly what university elective to take. |

## 7. The Job Application Lifecycle: Phase Breakdown
**Phase 1: Job Sourcing (Finding Opportunities)**
- Goal: High-volume discovery of relevant roles.
- Top Apps: LinkedIn, Indeed, Glassdoor, Otta (Tech-focused), Handshake (Student-exclusive).
- The Drawback: "Search Fatigue." Users see the same 10 jobs across all platforms. LinkedIn/Indeed are filled with "Ghost Jobs" (ads for jobs that don't exist).

**Phase 2: Job Description (JD) Evaluation**
- Goal: Determining "Am I a match?" before wasting time.
- Top Apps: JobScan (Keyword scoring), Teal (Matching), JobRight.ai (AI scoring), Simplify.
- The Accuracy Issue: "Context Blindness." Simplify and LinkedIn often count keywords (e.g., "Product") but miss seniority or domain.

**Phase 3: Resume Development**
- Goal: Tailoring the resume to a specific JD.
- Top Apps: JobRight.ai, Kickresume, Simplify (Simplified tailoring).
- The Drawback: "The AI Signature." JobRight's aggressive rewriting often results in resumes that feel generic or "too perfect," which recruiters now flag as AI-spam.

**Phase 4: Job Applying Automation**
- Goal: Removing form-filling friction.
- Top Apps: Simplify (Browser Extension), JobRight.ai (Auto-apply), LazyApply.
- The Drawback: "Form Errors." Simplify is great for name/email but often fails on complex questions.

**Phase 5: Job Tracking**
- Goal: Organizing follow-ups.
- Top Apps: Teal (The leader), Huntr, Simplify (Built-in dashboard).
- The Drawback: Manual Maintenance. If the user applies outside the extension, they often forget to log it.

**Phase 6: Interview Prep**
- Goal: Mock interviews and question generation.
- Top Apps: JobRight (Orion Chatbot), Google Interview Warmup.
- The Drawback: "The Scripted Trap." AI-prep often leads students to memorize generic answers, making them sound robotic.

## 8. Matching Accuracy: The Reality of "AI Matches"
Most incumbent platforms rely on simple Natural Language Processing (NLP) or basic keyword extraction, creating the illusion of a match while frustrating both recruiters and students. By moving from a "Keyword Score" to a "Verified Syllabus Mapping," your platform restores trust to the recruiting pipeline (see Section 6 for full platform breakdown).

## 10. Strategic Advantage Plan (Phase-by-Phase)
**Phase 1: Sourcing (Solution to "Ghost Jobs")**
- Your Advantage: Alumni-Sourced Prioritization. Use university data to prioritize jobs where alumni are employed.

**Phase 2: JD Evaluation (Solution to "Domain Blindness")**
- Your Advantage: Curriculum-Gated Matching. Only label a "Strong Match" if verified course modules match the JD.

**Phase 3: Resume Development (Solution to "AI Lying/Spam")**
- Your Advantage: The "Verified Project" Badge. Bullets pull from a library of "University-Verified Projects."

**Phase 4: Job Automation (Solution to "Form Errors")**
- Your Advantage: Official Student Record Sync. Use official university records for visa/graduation status auto-fill.

**Phase 5: Gap Analysis (Solution to "Generic Advice")**
- Your Advantage: Prescriptive Course Mapping. Link missing tools to the exact university course that teaches them.

## 11. Current Technical Architecture (The MVP Backend)
The current `Job_Automation` codebase establishes a powerful foundation for the "Frictionless Evaluation" model, completely bypassing the "copy-paste" problem seen in Gemini or Simplify.

**The Multi-Resume Routing Engine:**
1. **Data Ingestion (`google_sheets_client.py`):** Jobs are automatically scraped and deposited into a database/sheet. The system monitors this feed asynchronously without user input.
2. **Context Compilation (`evaluate_jobs.py`):** Instead of a single resume, the engine loads a full directory of YAML-based student profiles (e.g., `role_tpm.yaml`, `role_ba.yaml`, `role_manager.yaml`).
3. **The 3-Tier LLM Router (`llm_router.py`):** To ensure 100% uptime and cost efficiency, the system uses a tiered fallback mechanism:
   - **Tier 1 (Speed & Cost):** Gemini 2.0 Flash handles the bulk of continuous background evaluations.
   - **Tier 2 (Reliability Fallback):** OpenAI `gpt-4o-mini` catches any Rate Limit (429) errors from Tier 1.
   - **Cloud Resiliency:** Hybrid cloud routing via Gemini and OpenRouter ensures high uptime.
4. **Intelligent Output:** The system does not just score the job; it tells the student *exactly which of their specific resumes* (e.g., "Use the GTM Resume") yields the highest probability of an interview.

## 12. Analyzing JobRight's Sourcing & GitHub Strategy
**How JobRight Sources (The "GitHub Funnel"):**
- Frequency: JobRight runs a scraper that updates their GitHub repos (e.g., 2026-Engineering-New-Grad) every 24 hours. These repositories act as "Live Feeds" to lure students into their app.
- The Weakness: These repos only list a "fraction" of jobs. They are Manual Curation masquerading as Full Automation.
- Major Drawback: Because they rely on high-volume scraping, they pick up many reposted/duplicate jobs and "Ghost Jobs" from LinkedIn. They prioritize newness over quality.

**Building a "Better" Sourcing Platform:**
- Direct ATS Scraping (The "Verified Source"): Instead of scraping LinkedIn (which is full of spam), your platform should prioritize scraping direct company career pages (Greenhouse, Workday) and University-Partner Portals.
- "Warm" Sourcing (Alumni Loop): JobRight is "Cold Sourcing" (anyone can see it). You can implement "Warm Sourcing" where jobs are pulled from companies that specifically hired UTA students last year.
- Internal University "Shadow Market": Universities often have "hidden" job postings from donors or local partners that never hit LinkedIn. By being B2B, you gain access to this "Shadow Market" that JobRight's scrapers will never find.
- Open Source Strategy: Instead of just listing jobs on GitHub (like JobRight), you can open-source your "JD-to-Syllabus Parser." This builds massive credibility with the developer/academic community and makes you the "Standard" for educational job matching.
