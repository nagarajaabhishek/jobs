import json
import os
from datetime import datetime, timedelta
import logging


def cleanup_jd_cache(cache_path, ttl_days=30):
    """
    Removes entries from jd_cache.json that are older than ttl_days.
    Expects cache format: { "url": { "jd": "...", "timestamp": "YYYY-MM-DD" } }
    Also handles migration from old format: { "url": "description" }
    """
    if not os.path.exists(cache_path):
        return 0, 0

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except Exception as e:
        logging.error(f"Error loading JD cache for cleanup: {e}")
        return 0, 0

    cutoff_date = datetime.now() - timedelta(days=ttl_days)
    new_cache = {}
    removed_count = 0
    migrated_count = 0

    for url, data in cache.items():
        if isinstance(data, str):
            # Migrate old format to new format with current timestamp.
            new_cache[url] = {
                "jd": data,
                "timestamp": datetime.now().strftime("%Y-%m-%d"),
            }
            migrated_count += 1
        elif isinstance(data, dict):
            ts_str = data.get("timestamp")
            try:
                ts = datetime.strptime(str(ts_str), "%Y-%m-%d")
                if ts >= cutoff_date:
                    new_cache[url] = data
                else:
                    removed_count += 1
            except (ValueError, TypeError):
                # If timestamp is invalid, keep it but normalize timestamp to now.
                data["timestamp"] = datetime.now().strftime("%Y-%m-%d")
                new_cache[url] = data
        else:
            removed_count += 1

    if removed_count > 0 or migrated_count > 0:
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(new_cache, f, ensure_ascii=False, indent=0)
        except Exception as e:
            logging.error(f"Error saving cleaned JD cache: {e}")

    return removed_count, migrated_count

