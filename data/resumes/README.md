# Resumes (canonical location)

LaTeX sources, PDFs, career profiles, and cover letters for **Abhishek** live in the resume agent tree, not under this folder:

`core_agents/resume_agent/Resume_Building/Abhishek/<RoleName>/`

Examples:

- Master: `.../Abhishek/Master/Abhishek_Nagaraja_Master_Resume.tex` (and `.pdf`)
- TPM: `.../Abhishek/Product/Abhishek_Nagaraja_TPM_Resume.tex`
- Tailored outputs: `.../Resume_Building/Tailored/<Profile>/<JD_STEM>/` (see repo README)
- Generator fallback (bare `meta.filename`): `.../Abhishek/Generated/` — PDFs from `generate_resume.py` / `generate_cover_letter.py` always land in the **same directory as the `.tex`** (under the person folder).

This directory is kept as a **pointer** so `data/` stays about profiles, digests, and pipeline artifacts without duplicating resume assets.
