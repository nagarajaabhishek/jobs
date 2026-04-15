import os
import sys
from unittest.mock import Mock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.scrapers.recruitee_scraper import RecruiteeScraper


def _resp(payload, status=200):
    m = Mock()
    m.status_code = status
    m.json.return_value = payload
    m.raise_for_status.return_value = None
    return m


@patch("apps.cli.legacy.scrapers.recruitee_scraper.requests.get")
def test_recruitee_scrape_company_normalizes(mock_get):
    mock_get.return_value = _resp(
        {
            "offers": [
                {
                    "title": "Product Manager",
                    "careers_url": "https://acme.recruitee.com/o/product-manager",
                    "company_name": "Acme",
                    "location": "New York",
                    "country": "US",
                    "description": "desc",
                }
            ]
        }
    )

    jobs = RecruiteeScraper(companies=["acme"]).scrape_company("acme")
    assert len(jobs) == 1
    assert jobs[0]["source"] == "ATS_Recruitee"
    assert jobs[0]["location"] == "New York, US"


@patch("apps.cli.legacy.scrapers.recruitee_scraper.requests.get")
def test_recruitee_skips_invalid_rows(mock_get):
    mock_get.return_value = _resp({"offers": [{"title": "Missing URL"}]})
    jobs = RecruiteeScraper(companies=["acme"]).scrape_company("acme")
    assert jobs == []
