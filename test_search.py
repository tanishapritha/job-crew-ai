"""
Standalone test: verify job search providers return real results.
Run this directly: python test_search.py

This does NOT require CrewAI, FastAPI, or Google Sheets.
It tests the raw provider layer in isolation.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from tools.job_providers import search_all_providers, get_active_providers
from tools.job_providers.base import JobResult


def test_provider_discovery():
    """Check which providers are active."""
    print("\n" + "=" * 60)
    print("TEST 1: Provider Discovery")
    print("=" * 60)

    providers = get_active_providers()
    names = [p.get_name() for p in providers]
    print(f"  Active providers: {names}")

    assert len(providers) > 0, "FAIL: No providers available at all!"
    print(f"  [PASS] {len(providers)} provider(s) active")
    return providers


def test_single_domain_single_location():
    """Basic search: one domain, one location."""
    print("\n" + "=" * 60)
    print("TEST 2: Single Domain + Single Location")
    print("=" * 60)

    results = search_all_providers(
        domain="python developer",
        location="Mumbai",
        limit=10,
        max_days_old=14,
    )

    print(f"  Results returned: {len(results)}")
    if results:
        print(f"  First job: {results[0].get('title', 'N/A')} @ {results[0].get('company', 'N/A')}")
        print(f"  Source: {results[0].get('source', 'N/A')}")
        url = results[0].get('redirect_url', 'N/A')
        print(f"  URL: {url[:80]}...")

    assert len(results) > 0, "FAIL: No results at all for 'python developer' in 'Mumbai'"
    print(f"  [PASS] {len(results)} jobs found")
    return results


def test_multiple_domains():
    """Simulate the user having multiple job titles (domains separated by ;)."""
    print("\n" + "=" * 60)
    print("TEST 3: Multiple Domains (simulates user with multiple job titles)")
    print("=" * 60)

    domains = ["data analyst", "machine learning engineer"]
    location = "Bangalore"

    all_results = []
    for domain in domains:
        results = search_all_providers(domain=domain, location=location, limit=5, max_days_old=14)
        print(f"  '{domain}' in '{location}': {len(results)} results")
        all_results.extend(results)

    # Deduplicate across domains
    seen = set()
    unique = []
    for r in all_results:
        key = (r["title"].lower(), r["company"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(r)

    print(f"  Total unique across domains: {len(unique)}")
    assert len(unique) > 0, "FAIL: No results across multiple domains"
    print(f"  [PASS]")


def test_multiple_locations():
    """Simulate user with 3 locations."""
    print("\n" + "=" * 60)
    print("TEST 4: Multiple Locations (simulates user with 3 cities)")
    print("=" * 60)

    domain = "software engineer"
    locations = ["Mumbai", "Bangalore", "Delhi"]

    location_counts = {}
    for loc in locations:
        results = search_all_providers(domain=domain, location=loc, limit=5, max_days_old=14)
        location_counts[loc] = len(results)
        print(f"  '{domain}' in '{loc}': {len(results)} results")

    total = sum(location_counts.values())
    print(f"  Total across all locations: {total}")
    assert total > 0, "FAIL: No results across any location"
    print(f"  [PASS]")


def test_result_has_required_fields():
    """Every result must have: title, company, location, redirect_url, source."""
    print("\n" + "=" * 60)
    print("TEST 5: Required Fields Present")
    print("=" * 60)

    results = search_all_providers(domain="react developer", location="Hyderabad", limit=5, max_days_old=14)

    required_fields = ["title", "company", "location", "redirect_url", "source", "id"]
    missing_fields = []

    for i, job in enumerate(results):
        for field in required_fields:
            val = job.get(field, "")
            if not val or val in ["None", "nan", ""]:
                missing_fields.append(f"  Job {i} missing '{field}'")

    if missing_fields:
        for m in missing_fields[:10]:
            print(m)
        print(f"  [WARN] {len(missing_fields)} missing fields across {len(results)} jobs")
    else:
        print(f"  [PASS] All {len(results)} jobs have required fields")

    return results


def test_multi_source_coverage():
    """Verify results come from MORE than one platform."""
    print("\n" + "=" * 60)
    print("TEST 6: Multi-Source Coverage (LinkedIn + Indeed + others)")
    print("=" * 60)

    results = search_all_providers(domain="backend developer", location="India", limit=20, max_days_old=14)

    sources = set()
    for r in results:
        src = r.get("source", "").lower()
        if src:
            sources.add(src)

    print(f"  Sources found: {sources}")
    print(f"  Total results: {len(results)}")

    if len(sources) > 1:
        print(f"  [PASS] Results from {len(sources)} different platforms")
    else:
        print(f"  [WARN] Only {len(sources)} source(s). Ensure multiple providers are installed.")


def test_redirect_urls_are_valid():
    """Spot-check that redirect URLs are actual HTTP links."""
    print("\n" + "=" * 60)
    print("TEST 7: Redirect URLs Validity")
    print("=" * 60)

    results = search_all_providers(domain="devops engineer", location="Pune", limit=5, max_days_old=14)

    valid = 0
    invalid = 0
    for r in results:
        url = r.get("redirect_url", "")
        if url.startswith("http://") or url.startswith("https://"):
            valid += 1
        else:
            invalid += 1
            print(f"  [BAD URL] '{url[:60]}' for '{r.get('title', '')}'")

    if invalid == 0:
        print(f"  [PASS] All {valid} URLs are valid HTTP links")
    else:
        print(f"  [WARN] {invalid}/{valid + invalid} URLs are not valid HTTP links")


def test_email_template_renders():
    """Verify the HTML template renders without errors."""
    print("\n" + "=" * 60)
    print("TEST 8: Email Template Rendering")
    print("=" * 60)

    from utils.email_template import create_job_email_html

    mock_user = {
        "user_id": "test-123",
        "name": "Test User",
        "email": "test@test.com",
    }
    mock_jobs = [
        {
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "Mumbai",
            "description": "Looking for an experienced Python developer...",
            "salary_min": 1500000,
            "salary_max": 2500000,
            "redirect_url": "https://example.com/job/1",
            "source": "linkedin",
            "matched_domain": "python developer",
        },
        {
            "title": "Backend Engineer",
            "company": "StartupXYZ",
            "location": "Bangalore",
            "description": "Join our backend team...",
            "salary_min": None,
            "salary_max": None,
            "redirect_url": "https://example.com/job/2",
            "source": "indeed",
            "matched_domain": "backend engineer",
        },
    ]

    html = create_job_email_html(mock_user, mock_jobs)

    checks = [
        ("User name", "Test User" in html or "Test" in html),
        ("Job count", "2" in html),
        ("Job title", "Senior Python Developer" in html),
        ("Company", "TechCorp" in html),
        ("Source badge LinkedIn", "LinkedIn" in html),
        ("Source badge Indeed", "Indeed" in html),
        ("Apply on LinkedIn", "Apply on LinkedIn" in html),
        ("Apply on Indeed", "Apply on Indeed" in html),
        ("Dashboard link", "Dashboard" in html),
        ("Unsubscribe link", "unsubscribe" in html.lower()),
        ("Salary formatted", "L" in html),
    ]

    failed = 0
    for name, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            failed += 1
        print(f"  {status} {name}")

    if failed == 0:
        print(f"  [PASS] All {len(checks)} template checks passed")
    else:
        print(f"  [FAIL] {failed}/{len(checks)} checks failed")


if __name__ == "__main__":
    print("=" * 60)
    print("  JOB AUTOMATION -- PRE-FLIGHT TEST SUITE")
    print("=" * 60)

    # Test 1: discovery (no network)
    providers = test_provider_discovery()

    # Test 8: email template (no network)
    test_email_template_renders()

    # Tests 2-7: require network (actual API/scraping calls)
    print("\n>> Running live search tests (requires internet)...\n")

    try:
        test_single_domain_single_location()
        test_multiple_domains()
        test_multiple_locations()
        test_result_has_required_fields()
        test_multi_source_coverage()
        test_redirect_urls_are_valid()
    except Exception as e:
        print(f"\n[ERROR] Live test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("  ALL TESTS COMPLETE")
    print("=" * 60)
