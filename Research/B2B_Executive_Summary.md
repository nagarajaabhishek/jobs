# Executive Summary: The Curriculum-to-Career Intelligence Platform

## The Problem: The "Black Box" of Student Success
Universities currently operate with a lagging indicator of success. Platforms like Handshake or homegrown career portals are optimized for **employer volume**, not **student improvement**. When a student applies to 50 jobs and gets rejected from all of them, the university has zero visibility into *why*. Department heads cannot adjust syllabi to meet real-time market demands because they do not have granular data on where their student's skill gaps lie.

At the same time, students are frustrated by "Search Fatigue" and the hallucination-prone AI tools (like JobRight.ai) that rewrite their resumes with fake jargon just to pass ATS filters—which recruiters are increasingly blacklisting.

## The Solution: Frictionless, Curriculum-Gated Matching
Our platform acts as an **Intelligence Layer** that sits above existing sourcing methods. 

Instead of a student guessing which of their skills align with a job, our platform automatically ingests open roles from target employers and asynchronously maps them against the student's *verified university profile*. 

**The Dual-Sided Value Proposition:**
1. **For the Student (B2C):** A single daily feed of high-probability jobs from companies that actively hire their alumni. The platform automatically evaluates the job against *all* of the student's tailored resumes (e.g., TPM vs. Business Analyst) and tells them exactly which resume to submit. Zero copy-pasting, zero guessing.
2. **For the University (B2B):** Actionable, real-time analytics. If 60% of graduating Engineering students are failing to match with DFW-area Project Management roles because they lack Agile/Scrum skills, the Department Head is immediately notified and can add a 1-week Scrum module to an existing elective. This closes the gap, increases hiring rates, and provides hard data for ABET/AACSB accreditation.

## The Strategy: Land and Expand
We are adopting a "Warm Sourcing" approach, bypassing the generic noise of LinkedIn/Handshake.
- **Phase 1 (The Pilot):** Target highly measurable, technical programs at the **University of Texas at Arlington (UTA)**. Prove the curriculum ROI using our background evaluation engine (`evaluate_jobs.py` + `llm_router.py`).
- **Phase 2 (The Expansion):** Scale to **UT Dallas (UTD)**. UTD utilizes Handshake as an exclusive platform, creating massive institutional inertia. We will position our platform as the necessary intelligence layer that sits *on top* of Handshake to actually deliver curriculum feedback.
- **Phase 3 (The Ecosystem):** Integrate directly with University LMS (Canvas/Blackboard) for automated project ingestion across the entire UT System.

## The Competitive Moat: Authenticity Over Volume
Competitors like JobRight.ai optimize for speed, leading to AI Hallucinations that recruiters reject. We optimize for **Verifiability**. By gating our matching logic against a student's actual university transcript and graded projects, we restore trust to the recruiter pipeline. Our B2C competitors fundamentally cannot access the internal syllabus data that powers our B2B insights.
