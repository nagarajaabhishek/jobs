import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import yaml


def _read_yaml(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_skill(s: str) -> str:
    return (
        str(s or "")
        .strip()
        .lower()
        .replace("*", "")
        .replace(".", "")
        .replace("/", " ")
    )


def _top_items(d: Dict[str, Any], n: int = 20) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    for k, v in (d or {}).items():
        try:
            out.append((str(k), int(v)))
        except Exception:
            continue
    out.sort(key=lambda x: (-x[1], x[0].lower()))
    return out[:n]


def _theme_for_skill(skill: str) -> str:
    s = _normalize_skill(skill)
    # Lightweight grouping to help users and future UI sections.
    if any(x in s for x in ["sql", "analytics", "tableau", "power bi", "excel", "data", "metrics"]):
        return "data_analytics"
    if any(x in s for x in ["python", "pandas", "numpy", "ml", "machine learning", "model"]):
        return "data_science"
    if any(x in s for x in ["aws", "gcp", "azure", "kubernetes", "docker", "terraform", "ci/cd"]):
        return "cloud_platform"
    if any(x in s for x in ["jira", "confluence", "figma", "notion", "mural"]):
        return "pm_tooling"
    if any(x in s for x in ["api", "microservice", "backend", "frontend", "react"]):
        return "software_eng_basics"
    if any(x in s for x in ["gtm", "pricing", "growth", "marketing", "seo", "crm", "salesforce"]):
        return "go_to_market"
    return "other"


def _infer_sectors_from_tech(tech_terms: List[str]) -> List[Dict[str, Any]]:
    """
    Heuristic sector inference from observed tech stack terms.
    This is intentionally conservative (platform UI can refine later).
    """
    terms = {_normalize_skill(t) for t in tech_terms if t}
    hits: Dict[str, int] = {}

    def bump(sector: str, k: int = 1) -> None:
        hits[sector] = hits.get(sector, 0) + k

    for t in terms:
        if any(x in t for x in ["hipaa", "hl7", "epic", "cerner"]):
            bump("healthcare")
        if any(x in t for x in ["pci", "sox", "fraud", "risk", "trading"]):
            bump("fintech")
        if any(x in t for x in ["kafka", "spark", "databricks", "snowflake"]):
            bump("data_platforms")
        if any(x in t for x in ["shopify", "magento", "commerce", "stripe"]):
            bump("ecommerce")
        if any(x in t for x in ["unity", "unreal", "gaming"]):
            bump("gaming")
        if any(x in t for x in ["adtech", "ads", "attribution"]):
            bump("adtech")
        if any(x in t for x in ["ai", "llm", "openai", "vertex", "bedrock"]):
            bump("ai_products")

    out = [{"sector": s, "signal_strength": n} for s, n in sorted(hits.items(), key=lambda x: (-x[1], x[0]))]
    return out[:6]


@dataclass(frozen=True)
class CareerStrategyArtifact:
    date: str
    profile_name: str
    target_roles: List[Dict[str, Any]]
    target_sectors: List[Dict[str, Any]]
    top_skill_gaps: List[Dict[str, Any]]
    skill_gap_themes: List[Dict[str, Any]]
    proof_of_work_projects: List[Dict[str, Any]]


class CareerStrategyAgent:
    """
    Generates role + sector recommendations and an upskilling roadmap.

    File-first output (Markdown + JSON) so it can later become a platform page.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.dense_matrix_path = os.environ.get("DENSE_MATRIX_PATH") or os.path.join(project_root, "data", "dense_master_matrix.json")
        self.skill_gaps_path = os.path.join(project_root, "data", "skill_gap_frequency.yaml")
        self.company_insights_path = os.path.join(project_root, "data", "company_insights.yaml")
        self.salary_benchmarks_path = os.path.join(project_root, "data", "salary_benchmarks.yaml")

    def _load_dense_matrix(self) -> Dict[str, Any]:
        return _read_json(self.dense_matrix_path)

    def build(self, *, top_n_skills: int = 20) -> CareerStrategyArtifact:
        dense = self._load_dense_matrix()
        traits = dense.get("global_traits") or {}
        profile_name = str(traits.get("name") or "Candidate")

        # Market signals
        skill_gaps = _read_yaml(self.skill_gaps_path)
        skill_gaps_top = _top_items(skill_gaps, n=top_n_skills)

        company_insights = _read_yaml(self.company_insights_path)
        all_tech: List[str] = []
        if isinstance(company_insights, dict):
            for _, v in company_insights.items():
                if isinstance(v, dict):
                    all_tech.extend(list(v.get("tech_stack") or []))

        # Role anchors
        role_variants = dense.get("role_variants") or {}
        role_recs: List[Dict[str, Any]] = []
        missing_skills_norm = {_normalize_skill(s) for s, _ in skill_gaps_top}

        for role_key, role_data in role_variants.items():
            core_skills = list(role_data.get("core_skills") or [])
            # Pull tokens from "Category: skill1, skill2" strings.
            tokens: List[str] = []
            for line in core_skills:
                for part in str(line).split(":")[-1].split(","):
                    t = _normalize_skill(part)
                    if t:
                        tokens.append(t)
            token_set = set(tokens)
            overlap = len(token_set & missing_skills_norm)
            role_recs.append(
                {
                    "role_variant": str(role_key),
                    "focus": str(role_data.get("focus") or ""),
                    "market_gap_overlap": overlap,
                }
            )

        role_recs.sort(key=lambda r: (-int(r.get("market_gap_overlap") or 0), str(r.get("role_variant") or "")))

        # Skill themes
        themes: Dict[str, List[Dict[str, Any]]] = {}
        for skill, count in skill_gaps_top:
            theme = _theme_for_skill(skill)
            themes.setdefault(theme, []).append({"skill": skill, "count": count})
        themed = [{"theme": t, "skills": items} for t, items in sorted(themes.items(), key=lambda x: (-len(x[1]), x[0]))]

        # Proof-of-work project suggestions (template-like, grounded in missing skills)
        projects: List[Dict[str, Any]] = []
        for theme in [t["theme"] for t in themed[:4]]:
            if theme == "data_analytics":
                projects.append(
                    {
                        "title": "Metric-driven product dashboard case study",
                        "outcome": "Ship a public dashboard + write-up showing metrics, funnels, cohorts, and decisions.",
                        "skills": ["SQL", "Dashboarding", "Experiment design"],
                    }
                )
            elif theme == "cloud_platform":
                projects.append(
                    {
                        "title": "Cloud-native data pipeline (mini)",
                        "outcome": "Deploy a small pipeline with orchestration, monitoring, and cost notes.",
                        "skills": ["Docker", "Kubernetes", "Cloud basics", "Observability"],
                    }
                )
            elif theme == "pm_tooling":
                projects.append(
                    {
                        "title": "PRD + Jira delivery simulation",
                        "outcome": "Create PRD, backlog, sprint plan, and a demo video walkthrough.",
                        "skills": ["Jira", "PRD writing", "Stakeholder comms"],
                    }
                )
            elif theme == "go_to_market":
                projects.append(
                    {
                        "title": "GTM teardown + positioning memo",
                        "outcome": "Pick a product, write positioning, pricing hypothesis, and experiment plan.",
                        "skills": ["GTM", "Pricing", "Growth experiments"],
                    }
                )

        # Sectors from observed tech
        sectors = _infer_sectors_from_tech(all_tech)

        date = datetime.now().strftime("%Y-%m-%d")
        return CareerStrategyArtifact(
            date=date,
            profile_name=profile_name,
            target_roles=role_recs[:6],
            target_sectors=sectors,
            top_skill_gaps=[{"skill": s, "count": c} for s, c in skill_gaps_top],
            skill_gap_themes=themed,
            proof_of_work_projects=projects,
        )

    def write_outputs(
        self,
        artifact: CareerStrategyArtifact,
        *,
        output_dir: str | None = None,
    ) -> Tuple[str, str]:
        out_dir = output_dir or os.path.join(self.project_root, "data", "strategy")
        os.makedirs(out_dir, exist_ok=True)
        base = f"career_strategy_{artifact.date}"
        json_path = os.path.join(out_dir, f"{base}.json")
        md_path = os.path.join(out_dir, f"{base}.md")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(artifact.__dict__, f, ensure_ascii=False, indent=2)

        md = []
        md.append(f"# Career Strategy ({artifact.date})")
        md.append("")
        md.append(f"Profile: **{artifact.profile_name}**")
        md.append("")
        md.append("## Target roles to prioritize")
        for r in artifact.target_roles:
            md.append(f"- **{r.get('role_variant')}** (market-gap overlap: {r.get('market_gap_overlap')})")
            focus = str(r.get("focus") or "").strip()
            if focus:
                md.append(f"  - {focus}")
        md.append("")
        md.append("## Target sectors (lightweight inference)")
        if artifact.target_sectors:
            for s in artifact.target_sectors:
                md.append(f"- **{s.get('sector')}** (signal: {s.get('signal_strength')})")
        else:
            md.append("- Not enough tech-stack signal yet. Run more cycles to accumulate company insights.")
        md.append("")
        md.append("## Upskilling priorities (from recent JDs)")
        for item in artifact.top_skill_gaps[:15]:
            md.append(f"- **{item['skill']}** (mentions: {item['count']})")
        md.append("")
        md.append("## Skill themes")
        for t in artifact.skill_gap_themes:
            md.append(f"### {t['theme']}")
            for s in t["skills"][:10]:
                md.append(f"- {s['skill']} ({s['count']})")
            md.append("")
        md.append("## Proof-of-work projects (to legitimize gaps)")
        if artifact.proof_of_work_projects:
            for p in artifact.proof_of_work_projects:
                md.append(f"- **{p['title']}**")
                md.append(f"  - Outcome: {p['outcome']}")
                md.append(f"  - Skills: {', '.join(p['skills'])}")
        else:
            md.append("- Not enough signal yet.")
        md.append("")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md).rstrip() + "\n")

        return md_path, json_path

