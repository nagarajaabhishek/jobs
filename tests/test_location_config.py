import sys
import os
sys.path.append(os.getcwd())

from src.core.config import get_sourcing_config

def test_config():
    cfg = get_sourcing_config()
    print(f"Sourcing Config: {cfg}")
    locations = cfg.get("locations")
    print(f"Locations: {locations}")
    
    if isinstance(locations, dict):
        print("✅ SUCCESS: Locations is a dictionary.")
        for loc, target in locations.items():
            print(f"  - {loc}: {target}")
    else:
        print("❌ FAILURE: Locations is not a dictionary.")

if __name__ == "__main__":
    test_config()
