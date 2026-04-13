"""
Unified Job Search Tool for CrewAI.

This tool replaces the old single-API AdzunaAPITool. It fans out searches
across ALL registered job providers (Adzuna, JobSpy, etc.), deduplicates
results, and returns a unified list.

To add a new job source, you never touch this file — just add a provider
in tools/job_providers/.
"""

import json
from crewai.tools import tool
from tools.job_providers import search_all_providers


@tool("JobSearchTool")
def job_search_tool(input: str) -> list[dict]:
    """Search for jobs across ALL available job providers (Adzuna, JobSpy / LinkedIn / Indeed / Glassdoor, etc).
    Input: JSON string with {"domain": str, "location": str, "limit": int, "max_days_old": int}.
    Returns a unified, deduplicated list of job dicts from every active provider.
    """
    try:
        data = json.loads(input)
        domain = data.get("domain", "")
        location = data.get("location", "")
        limit = int(data.get("limit", 10))
        max_days_old = int(data.get("max_days_old", 7))

        results = search_all_providers(
            domain=domain,
            location=location,
            limit=limit,
            max_days_old=max_days_old,
        )

        print(f"[JobSearchTool] Total unified results for '{domain}' in '{location}': {len(results)}")
        return results

    except Exception as e:
        print(f"[JobSearchTool] Error: {e}")
        return [{"error": str(e)}]
