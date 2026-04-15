import os
import sys
from datetime import datetime


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


SSOT_PATH = os.path.join(PROJECT_ROOT, "docs", "CYCLE_SSOT.md")
BEGIN = "<!-- SSOT:BEGIN -->"
END = "<!-- SSOT:END -->"


def _render_mermaid() -> str:
    return """```mermaid
flowchart TD
  startNode[StartCycle] --> preflight[PreflightChecks]
  preflight -->|fail| stopPreflight[Stop:MissingPrereqs]
  preflight -->|pass| source[SourcingAgent:ScrapeJobSources]

  source --> staticFilter[StaticFiltersAndDedup]
  staticFilter --> jdFetch[JDResolutionSelectorOnly]

  jdFetch -->|verifiedJD_ok| writeSheet[WriteJobsToSheetAndJDCache]
  jdFetch -->|verifiedJD_missing| noJD[WriteRowStatus_NO_JD]

  writeSheet --> eval[EvaluationAgent:StrictJSON]
  eval -->|json_ok| persistEval[PersistVerdictAndEvidenceJSON]
  eval -->|json_invalid| needsReview[MarkNEEDS_REVIEW]

  persistEval --> calibrate[CalibrationOptional]
  calibrate --> tailor{TailorIfHighScore}
  tailor -->|yes| tailorAgent[TailorAgent:NonFabricationAndQA]
  tailor -->|no| hooks[CycleHooks]
  tailorAgent --> hooks

  hooks --> digest[DigestBuilderOptional]
  hooks --> careerStrategy[CareerStrategyOptional]
  digest --> endNode[EndCycle]
  careerStrategy --> endNode
```"""


def _render_checklist() -> str:
    lines = []
    lines.append("### Preflight checklist")
    lines.append(
        "- LLM key present for `evaluation.provider` (`OPENROUTER_API_KEY`, `GEMINI_API_KEY`, or `OPENAI_API_KEY`)"
    )
    lines.append("- `config/credentials.json` present (Sheets)")
    lines.append("- Profile present + compiled:")
    lines.append("  - `master_context.yaml` exists")
    lines.append("  - `dense_master_matrix.json` exists and is fresh")
    lines.append("")
    lines.append("### Hard gates")
    lines.append("- Evaluate only if `JD Verified = Y` (selector-only extraction)")
    lines.append("- If model output invalid: set `Status = NEEDS_REVIEW` and store raw/error in `Evidence JSON`")
    return "\n".join(lines)


def _write_block(existing: str, block: str) -> str:
    if BEGIN not in existing or END not in existing:
        raise RuntimeError(f"Missing SSOT markers in {SSOT_PATH}")
    pre = existing.split(BEGIN)[0]
    post = existing.split(END)[1]
    return pre + BEGIN + "\n" + block.rstrip() + "\n" + END + post


def generate() -> None:
    if not os.path.isfile(SSOT_PATH):
        raise FileNotFoundError(SSOT_PATH)
    with open(SSOT_PATH, "r", encoding="utf-8") as f:
        existing = f.read()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    block = []
    block.append(f"_Last generated: {now}_")
    block.append("")
    block.append(_render_mermaid())
    block.append("")
    block.append(_render_checklist())
    out = _write_block(existing, "\n".join(block))

    with open(SSOT_PATH, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Updated {SSOT_PATH}")


if __name__ == "__main__":
    generate()

