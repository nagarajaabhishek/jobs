import os
import sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from apps.cli.legacy.agents.career_strategy_agent import CareerStrategyAgent


def build_career_strategy() -> tuple[str, str]:
    agent = CareerStrategyAgent(project_root=PROJECT_ROOT)
    artifact = agent.build()
    md_path, json_path = agent.write_outputs(artifact)
    print(f"Wrote career strategy:\n- {md_path}\n- {json_path}")
    return md_path, json_path


if __name__ == "__main__":
    build_career_strategy()

