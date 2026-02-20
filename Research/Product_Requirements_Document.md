# Product Requirements Document (PRD): Job Alignment & Evaluation Platform

## 1. Executive Summary
**Vision:** To bridge the gap between higher education curricula and employer expectations by providing verifiable, curriculum-backed job matching and prescriptive gap analysis.
**Target Audience & Rollout:**
- Phase 1 (Pilot): University of Texas at Arlington (UTA) Students & Career Center.
- Phase 2 (Expansion): University of Texas at Dallas (UTD) and other regional institutions.
- Primary User Base: University Students (B2C adoption, free tier)
- Primary Revenue Source: University Administrations & Career Centers (B2B buyers)

## 2. Problem Statement
The current job application ecosystem is broken for entry-level talent:
- **Students** face "Search Fatigue" and "Context Blindness," applying to 100s of generic roles without knowing if their coursework actually prepared them for the job.
- **Employers** are overwhelmed by AI-generated "spam" resumes created by tools like JobRight.ai, which hallucinate skills to pass ATS filters, leading to recruiter trust deficits.
- **Universities** lack actionable data on how well their syllabi map to real-time market demands, relying on outdated First Destination Surveys.

## 3. Product Features & Requirements

### 3.1. Warm Sourcing Engine (Phase 1)
- **Description:** A targeted job scraper that sources roles exclusively from companies with a proven history of hiring alumni from the user's university.
- **Requirements:**
  - `Company Target List`: Ability to ingest a list of high-probability employers.
  - `ATS Direct Integrations`: Scrapers specifically built for Greenhouse, Workday, and Lever to bypass generic boards (LinkedIn/Indeed) and avoid "Ghost Jobs".
  - `The "Warm" Feed`: UI element showing the exact connection (e.g., "12 UTA Alumni hired here last year").

### 3.2. Automated "Frictionless" Evaluation Engine (Phase 2)
- **Description:** An LLM-powered engine that automatically evaluates a scraped Job Description (JD) against a student's entire portfolio of context files in the background, requiring zero copy/pasting from the user.
- **Requirements:**
  - `Multi-Context Mapping`: The system ingests the full directory of student data (e.g., `role_tpm.yaml`, `role_ba.yaml`, transcript data) and evaluates the JD against all possible profiles simultaneously.
  - `Intelligent Routing`: The system automatically recommends which specific internal resume the student should use to apply (e.g., "Use the Business Analyst profile, not the TPM profile").
  - `Zero UI-Friction`: Students do not manually trigger the evaluation by pasting text. The system evaluates jobs in the background as they hit the database, presenting the student with a pre-evaluated feed.
  - `Verification Badge`: Logic that flags a skill as "Verified" only if it maps to a completed course or graded project.
  - `Domain-Aware Matching`: Refusal to output a "High Match" if the JD requires senior-level years of experience, preventing the "LinkedIn Top Applicant Lie."

### 3.3. Prescriptive Gap Analysis (Phase 3/4)
- **Description:** Instead of a generic rejection, the system provides a roadmap of missing skills and exactly how to acquire them.
- **Requirements:**
  - `Student View (The Roadmap)`: Identifies missing JD requirements and maps them to specific university electives ("Enroll in IE 5301 to learn JIRA").
  - `Professor/Admin View (The Enrollment Driver)`: Aggregate dashboard showing which skills are trending in specific job markets and which courses successfully teach them. Data used for accreditation (ABET/AACSB) and syllabus updates.

### 3.4. Authentic Resume Generation
- **Description:** A resume builder that constructs tailored resumes without Hallucination.
- **Requirements:**
  - `Project Library Block`: Resumes are built from a verified block of university projects rather than AI-rewritten bullets.
  - `Anti-Bloat Formatting`: Strict enforcement of 1-page constraints and removal of repetitive AI adjectives ("Spearheaded," "Orchestrated").

## 4. Competitive Moat (Differentiator)
- **Data Exclusivity:** Handshake relies on manual employer partnerships; JobRight relies on public GitHub scraping. We rely on internal university curriculum data and verified alumni hiring loops.
- **Trust over Volume:** By prioritizing verified academic projects over AI-generated JD-spam, our candidates pass human recruiter screens at a higher rate.

## 5. MVP Scope (v1.0)
- Command-Line Interface (CLI) or basic Streamlit Dashboard.
- Input: User uploads Resume + Mocked University Transcript/Syllabus.
- Input: User provides a specific Target Company URL or Job Description.
- Output: "Warm" vs "Cold" indicator, Verified Match Score, and Prescriptive Gap Analysis.
