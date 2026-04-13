"""
Job Provider Registry.

All registered providers are tried in order during a search.
To add a new provider:
  1. Create your_provider.py in this directory
  2. Subclass JobProvider from base.py
  3. Import and register it below
"""

from tools.job_providers.base import JobProvider, JobResult
from tools.job_providers.adzuna_provider import AdzunaProvider
from tools.job_providers.jobspy_provider import JobSpyProvider

# ──────────────────────────────────────────────
# PROVIDER REGISTRY — add new providers here
# ──────────────────────────────────────────────
_ALL_PROVIDERS: list[JobProvider] = [
    AdzunaProvider(),
    JobSpyProvider(),
    # Future:
    # RemoteOKProvider(),
    # IndeedAPIProvider(),
    # LinkedInProvider(),
]


def get_active_providers() -> list[JobProvider]:
    """Returns only providers whose credentials / dependencies are available."""
    active = [p for p in _ALL_PROVIDERS if p.is_available()]
    names = [p.get_name() for p in active]
    print(f"[Registry] Active job providers: {names}")
    return active


def search_all_providers(
    domain: str,
    location: str,
    limit: int = 10,
    max_days_old: int = 7,
) -> list[dict]:
    """
    Fan out a search across every active provider, deduplicate by title+company,
    and return unified results.
    """
    providers = get_active_providers()
    if not providers:
        print("[Registry] WARNING: No job providers available!")
        return []

    per_provider_limit = max(5, limit // len(providers))
    all_jobs: list[JobResult] = []

    for provider in providers:
        try:
            results = provider.search(
                domain=domain,
                location=location,
                limit=per_provider_limit,
                max_days_old=max_days_old,
            )
            print(f"[{provider.get_name()}] Returned {len(results)} jobs for '{domain}' in '{location}'")
            all_jobs.extend(results)
        except Exception as e:
            print(f"[{provider.get_name()}] Error: {e}")

    # Deduplicate by normalised title + company
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.title.strip().lower(), job.company.strip().lower())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return [j.to_dict() for j in unique_jobs]
