import os
import yaml
from pathlib import Path

def get_python_files(directory_path, exclude_files=None):
    if exclude_files is None:
        exclude_files = ["__init__.py"]
    
    path = Path(directory_path)
    if not path.exists():
        return []
    
    return [f.stem for f in path.glob("*.py") if f.name not in exclude_files]

def generate_mermaid_diagram():
    # Base paths
    root_dir = Path(__file__).resolve().parent.parent.parent
    scrapers_dir = root_dir / "src" / "scrapers"
    agents_dir = root_dir / "src" / "agents"
    config_path = root_dir / "config" / "pipeline.yaml"

    # Read components
    scrapers = get_python_files(scrapers_dir)
    agents = get_python_files(agents_dir)
    
    # Read config
    config_data = {}
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not read pipeline.yaml: {e}")

    # Build Mermaid Diagram
    lines = [
        "```mermaid",
        "graph TD",
        "    %% Data Sources & Storage",
        "    Config[(pipeline.yaml)]",
        "    GoogleSheets[Google Sheets Output]",
        "    JDCache[(JD Cache)]",
        ""
    ]

    # Sourcing Layer
    lines.append("    %% Sourcing Layer")
    lines.append("    subgraph Sourcing Layer")
    for scraper in scrapers:
        # Give nicer names
        name = scraper.replace('_scraper', '').title() + " Scraper"
        lines.append(f"        {scraper}[{name}]")
    lines.append("    end")
    lines.append("")

    # Active Agents
    lines.append("    %% Evaluation & Agents")
    lines.append("    subgraph Evaluation & Processing Layer")
    for agent in agents:
        name = agent.replace('_', ' ').title()
        lines.append(f"        {agent}(({name}))")
    lines.append("        Filters[Job Filters & Normalization]")
    lines.append("        LLMRouter{LLM Router}")
    lines.append("    end")
    lines.append("")

    # Routing Connections
    lines.append("    %% Connections")
    lines.append("    Config -.-> sourcing_agent")
    
    for scraper in scrapers:
        lines.append(f"    {scraper} --> sourcing_agent")

    lines.append("    sourcing_agent --> Filters")
    lines.append("    Filters --> JDCache")
    lines.append("    JDCache --> evaluate_jobs")
    
    if "sponsorship_agent" in agents:
         lines.append("    sponsorship_agent --> evaluate_jobs")

    lines.append("    evaluate_jobs --> LLMRouter")
    lines.append("    evaluate_jobs --> GoogleSheets")
    
    lines.append("```")

    return "\n".join(lines)

if __name__ == "__main__":
    diagram = generate_mermaid_diagram()
    print("\n" + "="*50)
    print("Generated Architecture Diagram (Mermaid format)")
    print("="*50 + "\n")
    print(diagram)
    print("\n" + "="*50)
    print("Instructions: Copy the block above into your favorite markdown renderer")
    print("or https://mermaid.live to view your pipeline architecture visually.")
