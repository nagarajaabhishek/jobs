"""Load pipeline config from config/pipeline.yaml (optional)."""
import os
import yaml

_default = {
    "sourcing": {
        "queries": [
            "Product Manager", "Project Manager", "Program Manager",
            "Business Analyst", "Product Owner", "Scrum Master",
            "Strategy Operations", "GTM Manager",
        ],
        "locations": {
            "United States": 80,
            "Dubai": 20,
            "Remote": 50
        },
        "max_workers": 4,
        "ats_boards": {
            "greenhouse": ["canva", "discord", "figma"],
            "lever": ["netflix", "palantir", "discord"],
            "ashby": ["ashby", "notion", "figma", "linear", "vercel", "ramp"],
        },
    },
    "evaluation": {
        "provider": "gemini",
        "gemini_model": "gemini-1.5-pro-latest",
        "batch_eval_size": 4,
        "sheet_batch_size": 25,
        "limit": 300,
    },
}


def load_pipeline_config():
    """Load config from config/pipeline.yaml. Falls back to defaults if missing."""
    path = os.environ.get("PIPELINE_CONFIG")
    if not path:
        path = os.path.join(os.getcwd(), "config", "pipeline.yaml")
    if not os.path.isfile(path):
        return _default
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        
        # Merge logical blocks
        out = _default.copy()
        for key in ("sourcing", "evaluation", "filters"):
            if key in data:
                # If it's a dict, merge it. If it's a list (unlikely here but safety), replace it.
                if isinstance(_default.get(key), dict) and isinstance(data[key], dict):
                    out[key] = {**_default.get(key, {}), **data[key]}
                else:
                    out[key] = data[key]
            elif key not in out:
                out[key] = {}
        return out
    except Exception:
        return _default


def get_sourcing_config():
    return load_pipeline_config().get("sourcing", _default["sourcing"])


def get_evaluation_config():
    return load_pipeline_config().get("evaluation", _default["evaluation"])


def get_filters_config():
    """Returns the filters section for dynamic loading in job_filters.py."""
    return load_pipeline_config().get("filters", {})
