import os
import sys
import yaml
import logging
from typing import Optional, List, Dict
import re
import json

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.core.llm_router import LLMRouter

class ResumeAgent:
    """
    Intelligent Resume Tailoring Agent.
    Ingests a Master Context (career history) and a Job Description.
    Outputs a tailored LaTeX resume file optimized for ATS and 'Deep Matching'.
    """

    def __init__(self, master_context_path: str = "data/profiles/master_context.yaml"):
        self.master_context_path = master_context_path
        self.llm = LLMRouter()
        self.master_data = self._load_context()
        self.logger = logging.getLogger("ResumeAgent")

    def _load_context(self) -> Dict:
        if not os.path.exists(self.master_context_path):
            self.logger.error(f"Master context not found at {self.master_context_path}")
            return {}
        with open(self.master_context_path, 'r') as f:
            return yaml.safe_load(f)

    async def tailor_resume(self, jd_text: str, output_path: str, compile: bool = True) -> str:
        """
        Main entry point: Tailors the resume based on the JD.
        """
        self.logger.info("Starting resume tailoring process...")

        # 1. Analyze JD vs Master Context
        plan = await self._plan_content(jd_text)
        if not plan:
            self.logger.error("Content planning failed.")
            return ""

        # 2. Generate LaTeX Content
        latex_content = self._generate_latex(plan)

        # 3. Save .tex file
        with open(output_path, 'w') as f:
            f.write(latex_content)

        # 4. Optional: Compile to PDF
        if compile:
            pdf_path = self.compile_pdf(output_path)
            return pdf_path or output_path

        return output_path

    def compile_pdf(self, tex_path: str) -> Optional[str]:
        """
        Compiles the LaTeX file into a PDF using pdflatex.
        """
        import subprocess
        
        # Ensure we are in the directory of the .tex file
        dir_name = os.path.dirname(tex_path)
        base_name = os.path.basename(tex_path)
        file_name_no_ext = os.path.splitext(base_name)[0]
        
        self.logger.info(f"Compiling {tex_path} to PDF...")
        try:
            # Run pdflatex
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", base_name],
                cwd=dir_name,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.logger.error(f"LaTeX Compilation failed: {result.stdout}")
                return None
                
            pdf_path = os.path.join(dir_name, f"{file_name_no_ext}.pdf")
            self.logger.info(f"PDF successfully created: {pdf_path}")
            return pdf_path
        except Exception as e:
            self.logger.error(f"Error during PDF compilation: {e}")
            return None

    async def _plan_content(self, jd_text: str) -> Dict:
        """
        Uses LLM to select and rewrite content.
        """
        prompt = f"""
        You are an expert Resume Engineer. Your task is to extract and tailor content from a Master Career Context to match a target Job Description.

        JOB DESCRIPTION:
        {jd_text}

        MASTER CONTEXT (Full History):
        {yaml.dump(self.master_data)}

        OUTPUT REQUIREMENTS:
        1. Select the top 3 most relevant Work Experiences.
        2. Select the top 2 most relevant Projects.
        3. For each selected item, rewrite the bullets using the Google 'XYZ' formula (Accomplished [X] as measured by [Y], by doing [Z]).
        4. Focus on 'vibe-aligning' keywords from the JD into the bullets WITHOUT lying.
        5. Return the result as a JSON object with:
           - 'summary': A tailored 3-sentence summary.
           - 'experience': List of objects (company, role, location, dates, bullets).
           - 'projects': List of objects (name, date, bullets).
           - 'skills': Tailored skill categories.
        """
        
        system_prompt = (
            "You are a professional resume tailor. Output ONLY valid JSON. "
            "IMPORTANT: If you include quotes inside a string, escape them with a backslash. "
            "Do not include any conversational text or markdown blocks."
        )
        response_text, _ = self.llm.generate_content(system_prompt=system_prompt, user_prompt=prompt)
        
        # Robust JSON extraction
        try:
            # Clean possible markdown formatting and whitespace
            text = response_text.strip()
            
            # Find the JSON block if it's wrapped in markers or noise
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                text = match.group(1)
            
            return json.loads(text)
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}. Raw text: {response_text[:100]}...")
            return {}

    def _generate_latex(self, plan: Dict) -> str:
        """
        Fills a LaTeX template with the planned content.
        """
        template = r"""
\documentclass[9pt,letterpaper]{article}
\usepackage[parskip]{parskip}
\usepackage{array}
\usepackage{ifthen}
\usepackage{charter}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage[colorlinks=true, urlcolor=blue]{hyperref}
\usepackage[left=0.5in,top=0.25in,right=0.4in,bottom=0.2in]{geometry}
\usepackage[none]{hyphenat}

\pdfgentounicode=1
\pagestyle{empty}

\makeatletter
\def \name#1{\def\@name{#1}}
\def \@name {}
\def \printname { \begingroup \centerline{\bf \huge \@name} \endgroup }
\def \address #1{ \def \@address {#1} }
\def \printaddress { \begingroup \centerline{\@address} \endgroup }

\newenvironment{rSection}[1]{
  \vspace{0.5em}
  \textbf{\Large #1}
  \hrule
  \begin{list}{}{ \setlength{\leftmargin}{0em} }
  \item[]
}{
  \end{list}
}

\newenvironment{rSubsection}[4]{
 {\bf #1} \hfill {#2}
 \ifthenelse{\equal{#3}{}}{}{ \\ {\em #3} \hfill {\em #4} }
 \begin{itemize}[leftmargin=1.5em, labelsep=0.5em, itemsep=0.1em]
}{
 \end{itemize}
}
\makeatother

\name{Abhishek Nagaraja}
\address{Arlington, Texas \textbullet\ work.abhishekn@gmail.com \textbullet\ linkedin.com/in/abhisheknagaraja}

\begin{document}
\printname
\printaddress

\begin{rSection}{Summary}
{{SUMMARY}}
\end{rSection}

\begin{rSection}{Experience}
{{EXPERIENCE}}
\end{rSection}

\begin{rSection}{Projects}
{{PROJECTS}}
\end{rSection}

\begin{rSection}{Skills}
{{SKILLS}}
\end{rSection}

\end{document}
"""
        # Fill placeholders
        summary = plan.get('summary', '')
        
        exp_latex = ""
        for item in plan.get('experience', []):
            bullets = "\n".join([f"\\item {b}" for b in item.get('bullets', [])])
            exp_latex += f"\\begin{{rSubsection}}{{{item.get('company')}}}{{{item.get('dates')}}}{{{item.get('role')}}}{{{item.get('location')}}}\n{bullets}\n\\end{{rSubsection}}\n"

        proj_latex = ""
        for item in plan.get('projects', []):
            bullets = "\n".join([f"\\item {b}" for b in item.get('bullets', [])])
            proj_latex += f"\\begin{{rSubsection}}{{{item.get('name')}}}{{{item.get('date', '')}}}{{}}{{}}\n{bullets}\n\\end{{rSubsection}}\n"

        skills_latex = "\\begin{itemize}[leftmargin=1em]\n"
        for cat, slist in plan.get('skills', {}).items():
            if isinstance(slist, list):
                slist = ", ".join(slist)
            skills_latex += f"\\item \\textbf{{{cat}:}} {slist}\n"
        skills_latex += "\\end{itemize}"

        rendered = template.replace("{{SUMMARY}}", summary)
        rendered = rendered.replace("{{EXPERIENCE}}", exp_latex)
        rendered = rendered.replace("{{PROJECTS}}", proj_latex)
        rendered = rendered.replace("{{SKILLS}}", skills_latex)
        
        return rendered

if __name__ == "__main__":
    import asyncio
    agent = ResumeAgent()
    # Test path logic
