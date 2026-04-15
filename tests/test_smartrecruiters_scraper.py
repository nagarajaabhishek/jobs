import os
import sys
from unittest.mock import Mock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.scrapers.smartrecruiters_scraper import SmartRecruitersScraper


def _resp(payload, status=200):
    m = Mock()
    m.status_code = status
    m.json.return_value = payload
    m.raise_for_status.return_value = None
    return m


@patch("apps.cli.legacy.scrapers.smartrecruiters_scraper.requests.get")
def test_smartrecruiters_scrape_company_paginates(mock_get):
    mock_get.side_effect = [
        _resp({
            "content": [
                {
                    "id": "abc",
                    "name": "Product Manager",
                    "company": {"name": "Acme"},
                    "location": {"city": "Austin", "region": "TX", "country": "US"},
                }
            ],
            "totalFound": 2,
        }),
        _resp({
            "content": [
                {
                    "id": "def",
                    "name": "Business Analyst",
                    "location": {"city": "Remote"},
                }
            ],
            "totalFound": 2,
        }),
    ]

    jobs = SmartRecruitersScraper(companies=["acme"], page_size=1).scrape_company("acme")

    assert len(jobs) == 2
    assert jobs[0]["source"] == "ATS_SmartRecruiters"
    assert jobs[0]["url"].endswith("/acme/abc")
    assert jobs[1]["company"] == "acme"


@patch("apps.cli.legacy.scrapers.smartrecruiters_scraper.requests.get")
def test_smartrecruiters_scrape_all_aggregates(mock_get):
    mock_get.return_value = _resp({"content": [], "totalFound": 0})
    jobs = SmartRecruitersScraper(companies=["one", "two"]).scrape_all()
    assert jobs == []
    assert mock_get.call_count == 2
