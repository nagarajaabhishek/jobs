import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.job_filters import TITLE_INCLUSIONS
import yaml

def verify_config():
    print("\n--- Verifying Dynamic Configuration ---")
    yaml_path = "config/pipeline.yaml"
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    
    yaml_inclusions = config.get("filters", {}).get("inclusions", [])
    
    print(f"YAML Inclusions Count: {len(yaml_inclusions)}")
    print(f"Runtime Inclusions Count: {len(TITLE_INCLUSIONS)}")
    
    if len(yaml_inclusions) == len(TITLE_INCLUSIONS) and yaml_inclusions[0] == TITLE_INCLUSIONS[0]:
        print("✅ SUCCESS: Dynamic filters loaded correctly from pipeline.yaml")
    else:
        print("❌ FAILURE: Dynamic filters mismatch!")
        print(f"First YAML: {yaml_inclusions[0] if yaml_inclusions else 'N/A'}")
        print(f"First Runtime: {TITLE_INCLUSIONS[0] if TITLE_INCLUSIONS else 'N/A'}")

if __name__ == "__main__":
    verify_config()
