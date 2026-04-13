"""
JobSpy provider — scrapes LinkedIn, Indeed, Glassdoor, Google Jobs
via the python-jobspy library.

Google Jobs is included because it indexes Indian job boards like
Naukri, giving us coverage of that platform without a dedicated scraper.
"""

from tools.job_providers.base import JobProvider, JobResult

# python-jobspy is optional; gracefully degrade if not installed
try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False


class JobSpyProvider(JobProvider):
    """
    Scrapes multiple job boards (LinkedIn, Indeed, Glassdoor, Google Jobs)
    through a single python-jobspy call.

    Google Jobs indexes Naukri postings from India, so we get Naukri
    coverage indirectly through that channel.
    """

    # Which sites to scrape — google indexes naukri for Indian jobs
    SITES = ["indeed", "linkedin", "glassdoor", "google"]

    def get_name(self) -> str:
        return "JobSpy"

    def is_available(self) -> bool:
        return JOBSPY_AVAILABLE

    def search(
        self,
        domain: str,
        location: str,
        limit: int = 10,
        max_days_old: int = 7
    ) -> list[JobResult]:
        if not JOBSPY_AVAILABLE:
            print("[JobSpy] python-jobspy not installed, skipping.")
            return []

        try:
            df = scrape_jobs(
                site_name=self.SITES,
                search_term=domain,
                location=location,
                results_wanted=limit,
                hours_old=max_days_old * 24,  # jobspy uses hours
                country_indeed="India",
            )

            if df is None or df.empty:
                return []

            jobs = []
            for _, row in df.iterrows():
                desc = str(row.get("description", ""))
                if len(desc) > 300:
                    desc = desc[:297] + "..."

                # Normalise salary fields
                sal_min = None
                sal_max = None
                if row.get("min_amount") is not None:
                    try:
                        sal_min = float(row["min_amount"])
                    except (ValueError, TypeError):
                        pass
                if row.get("max_amount") is not None:
                    try:
                        sal_max = float(row["max_amount"])
                    except (ValueError, TypeError):
                        pass

                date_posted = str(row.get("date_posted", ""))
                site_name = str(row.get("site", "jobspy")).lower()

                jobs.append(JobResult(
                    id=f"jobspy_{site_name}_{row.get('id', '')}",
                    title=str(row.get("title", "")),
                    company=str(row.get("company_name", "Unknown")),
                    location=str(row.get("location", location)),
                    description=desc,
                    salary_min=sal_min,
                    salary_max=sal_max,
                    contract_type=str(row.get("job_type", "")),
                    created=date_posted,
                    redirect_url=str(row.get("job_url", "")),
                    source=site_name,
                    matched_domain=domain,
                ))

            return jobs

        except Exception as e:
            print(f"[JobSpy] Search failed for '{domain}' in '{location}': {e}")
            return []
