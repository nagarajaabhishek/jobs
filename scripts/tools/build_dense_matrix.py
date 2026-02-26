import os
import sys
import yaml
import json
from datetime import datetime
import re

# Add project root to path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

PROFILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "profiles")
OUTPUT_PATH = os.path.join(os.path.dirname(PROFILES_DIR), "dense_master_matrix.json")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "pipeline.yaml")

def calculate_yoe(experience_list):
    """Calculates total Years of Experience dynamically from start/end dates.
       Provides a normalized estimate by finding the absolute earliest start date
       to account for overlapping entrepreneurial/internship roles."""
    current_date = datetime.now()
    earliest_start = current_date
    
    # Simple month map for partial matches
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    def parse_date(date_str):
        date_str = date_str.lower().strip()
        if date_str in ['present', 'current', '']:
            return current_date
            
        # Extract year and month
        year_match = re.search(r'\d{4}', date_str)
        if not year_match: return None
        year = int(year_match.group())
        
        month = 1 # Default
        for m_name, m_num in months.items():
            if m_name in date_str:
                month = m_num
                break
                
        return datetime(year, month, 1)

    for exp in experience_list:
        try:
            start_str = str(exp.get('dates', '')).split('-')[0].strip()
            if not start_str: continue

            start = parse_date(start_str)
            
            if start and start < earliest_start:
                earliest_start = start
        except Exception as e:
            pass
            
    m_diff = (current_date.year - earliest_start.year) * 12 + (current_date.month - earliest_start.month)
    return round(m_diff / 12, 1)

def extract_core_achievements(master_data):
    """Extracts and deduplicates bullet points to save tokens natively."""
    achievements = []
    
    # Extract from Experience
    for exp in master_data.get('experience', []):
        company = exp.get('company', 'Unknown')
        for bullet in exp.get('bullet_points', []):
           achievements.append(f"[{company}] {bullet}")
           
    # Extract from Projects
    for proj in master_data.get('projects', []):
        name = proj.get('name', 'Project')
        desc = proj.get('description', '')
        if desc:
            achievements.append(f"[Project: {name}] {desc}")
            
    # Deduplicate while preserving order mostly
    seen = set()
    unique_achievements = []
    for ach in achievements:
        if ach not in seen:
            seen.add(ach)
            unique_achievements.append(ach)
            
    return unique_achievements

def build_dense_matrix():
    print("--- 🏗️ Building Dense Candidate Matrix ---")
    
    master_path = os.path.join(PROFILES_DIR, "master_context.yaml")
    if not os.path.exists(master_path):
        print(f"❌ Master profile not found at {master_path}")
        return
        
    with open(master_path, 'r') as f:
        master_data = yaml.safe_load(f)
        
    # Read explicit constraints from pipeline.yaml
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            cfg = yaml.safe_load(f) or {}
            
    constraints = cfg.get("candidate_constraints", {})
    
    # Prioritize manual config, fallback to dynamic calculation
    configured_yoe = constraints.get("years_of_experience")
    if configured_yoe and str(configured_yoe).lower() != 'auto':
        yoe = float(configured_yoe)
        print(f"Using Configured YOE Override: {yoe} years")
    else:
        yoe = calculate_yoe(master_data.get('experience', []))
        print(f"Calculated Estimated YOE: {yoe} years")
        
    visa = constraints.get("visa_status", "F-1 (Requires H1B Sponsorship)")
    clearance = constraints.get("clearance", "None")
    
    print(f"Candidate Traits -> YOE: {yoe} | Visa: {visa} | Clearance: {clearance}")
    
    dense_matrix = {
        "global_traits": {
            "name": master_data.get('personal_info', {}).get('name', 'Candidate'),
            "years_of_experience": yoe,
            "visa_status": visa,
            "clearance": clearance,
            "education": [f"{edu.get('degree')} from {edu.get('university')}" for edu in master_data.get('education', [])]
        },
        "core_achievements": extract_core_achievements(master_data),
        "role_variants": {}
    }
    
    # Extract Role Variants
    for filename in os.listdir(PROFILES_DIR):
        if filename.startswith("role_") and filename.endswith(".yaml"):
            role_key = filename.replace("role_", "").replace(".yaml", "").upper()
            filepath = os.path.join(PROFILES_DIR, filename)
            
            with open(filepath, 'r') as f:
                role_data = yaml.safe_load(f)
                
            # Extract pure keywords for this role
            role_skills = []
            for entry in role_data.get('skills', []):
                if isinstance(entry, dict):
                     skills = entry.get('skill_list') or entry.get('skills')
                     role_skills.append(f"{entry.get('category')}: {skills}")
                     
            dense_matrix["role_variants"][role_key] = {
                "focus": role_data.get('summary', ''),
                "core_skills": role_skills
            }
            print(f"Loaded variant: {role_key}")

    # Save Dense Matrix
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(dense_matrix, f, indent=2)
        
    file_size = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\n✅ Dense Matrix generated at {OUTPUT_PATH}")
    print(f"Size: {file_size:.1f} KB (Highly optimized for LLM Context)")


if __name__ == "__main__":
    build_dense_matrix()
