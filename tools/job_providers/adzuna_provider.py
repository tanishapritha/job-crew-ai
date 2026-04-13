"""Adzuna job search provider."""

import requests
import re
from config import settings
from tools.job_providers.base import JobProvider, JobResult


class AdzunaProvider(JobProvider):
    """Fetches jobs from the Adzuna aggregator API."""

    def get_name(self) -> str:
        return "Adzuna"

    def is_available(self) -> bool:
        return bool(
            getattr(settings, "ADZUNA_APP_ID", "")
            and settings.ADZUNA_APP_ID != "your_adzuna_app_id"
            and getattr(settings, "ADZUNA_API_KEY", "")
            and settings.ADZUNA_API_KEY != "your_adzuna_api_key"
        )

    def search(
        self,
        domain: str,
        location: str,
        limit: int = 10,
        max_days_old: int = 7
    ) -> list[JobResult]:
        url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
        params = {
            "app_id": settings.ADZUNA_APP_ID,
            "app_key": settings.ADZUNA_API_KEY,
            "results_per_page": limit,
            "what": domain,
            "where": location,
            "sort_by": "date",
            "max_days_old": max_days_old,
        }

        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            raw_results = resp.json().get("results", [])
        except Exception as e:
            print(f"[Adzuna] Search failed for '{domain}' in '{location}': {e}")
            return []

        jobs = []
        for r in raw_results:
            desc = r.get("description", "")
            # Strip HTML tags
            desc = re.sub(r"<[^>]+>", "", desc)
            if len(desc) > 300:
                desc = desc[:297] + "..."

            jobs.append(JobResult(
                id=f"adzuna_{r.get('id', '')}",
                title=r.get("title", ""),
                company=r.get("company", {}).get("display_name", "Unknown"),
                location=r.get("location", {}).get("display_name", location),
                description=desc,
                salary_min=r.get("salary_min"),
                salary_max=r.get("salary_max"),
                contract_type=r.get("contract_type", ""),
                created=r.get("created", ""),
                redirect_url=r.get("redirect_url", ""),
                source="adzuna",
                matched_domain=domain,
            ))

        return jobs
