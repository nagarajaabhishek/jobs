import os
import sys
from unittest.mock import patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core_agents.sourcing_agent.agent import SourcingAgent


def test_community_once_registers_new_sources_when_enabled():
    cfg = {
        "ats_boards": {"greenhouse": [], "lever": [], "ashby": []},
        "run_smartrecruiters_once": True,
        "smartrecruiters_companies": ["acme"],
        "run_recruitee_once": True,
        "recruitee_companies": ["acme"],
    }

    with patch("core_agents.sourcing_agent.agent.get_sourcing_config", return_value=cfg):
        agent = SourcingAgent(sheets_client=None)

    captured = []

    def _capture(raw_jobs, use_ai_filter=False):
        captured.append(raw_jobs)

    agent.normalize_and_save = _capture

    agent.community_scraper.scrape_all = lambda: []
    agent.jobright_scraper.scrape_all = lambda: []
    agent.arbeitnow_scraper.scrape = lambda queries=None: []
    agent.ats_scraper.scrape_all = lambda: []
    agent.remotive_scraper.scrape = lambda: []
    agent.remoteok_scraper.scrape = lambda: []
    agent.ashby_scraper.scrape_all = lambda: []
    agent.dice_scraper.scrape = lambda queries=None, locations=None, limit=20: []
    agent.smartrecruiters_scraper.scrape_all = lambda: [{"title": "PM", "company": "Acme", "url": "u", "location": "Remote", "source": "ATS_SmartRecruiters"}]
    agent.recruitee_scraper.scrape_all = lambda: [{"title": "BA", "company": "Acme", "url": "u2", "location": "Remote", "source": "ATS_Recruitee"}]

    with patch("core_agents.sourcing_agent.agent.get_sourcing_config", return_value=cfg):
        out = agent.scrape_community_sources_once(skip_jobright=True)

    assert len(out) == 2
    assert any(j[0]["source"] == "ATS_SmartRecruiters" for j in captured if j)
    assert any(j[0]["source"] == "ATS_Recruitee" for j in captured if j)
