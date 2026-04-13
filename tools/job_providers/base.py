"""
Base class for all job search providers.

To add a new job source:
  1. Create a new file in tools/job_providers/
  2. Subclass JobProvider
  3. Implement search() and get_name()
  4. Register it in tools/job_providers/__init__.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class JobResult:
    """Unified job result format across all providers."""
    id: str = ""
    title: str = ""
    company: str = "Unknown"
    location: str = ""
    description: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    contract_type: str = ""
    created: str = ""
    redirect_url: str = ""
    source: str = ""          # which provider found this
    matched_domain: str = ""  # the search domain that matched

    def to_dict(self) -> dict:
        return asdict(self)


class JobProvider(ABC):
    """
    Abstract base class every job API adapter must implement.
    
    Each provider is responsible for:
      - Querying its external API
      - Normalising results into JobResult objects
      - Handling its own rate limits and errors
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return a human-readable provider name, e.g. 'Adzuna', 'JobSpy'."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider has valid credentials / is usable."""
        ...

    @abstractmethod
    def search(
        self,
        domain: str,
        location: str,
        limit: int = 10,
        max_days_old: int = 7
    ) -> list[JobResult]:
        """
        Search for jobs matching the given domain and location.
        
        Args:
            domain: Job category / keyword (e.g. "python developer")
            location: Geographic location (e.g. "Mumbai")
            limit: Max number of results to return
            max_days_old: Only return jobs posted within this many days
            
        Returns:
            List of JobResult objects, already normalised.
        """
        ...
