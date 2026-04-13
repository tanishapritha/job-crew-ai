import json
import time
import math
from datetime import datetime
from crewai import Agent, Task, Crew, Process

from tools.sheets_tools import sheets_read_tool, sheets_write_tool, sheets_update_cell_tool
from tools.job_search_tool import job_search_tool
from tools.email_tool import send_email_tool
from utils.email_template import create_job_email_html

# ──────────────────────────────────────────────
# AGENTS
# ──────────────────────────────────────────────

user_loader = Agent(
    role="Active User Loader",
    goal="Retrieve all active users who are eligible for job emails",
    tools=[sheets_read_tool],
    backstory="Checks that the system is enabled and returns the list of users whose status is active and who have at least one domain and either a location or remote_jobs=true.",
    verbose=False
)

job_fetcher = Agent(
    role="Job Search and Filter Specialist",
    goal="Find fresh, relevant job listings for a given user from multiple job sources and filter them to match their preferences precisely",
    tools=[job_search_tool, sheets_write_tool],
    backstory=(
        "Queries multiple job providers (Adzuna, JobSpy/LinkedIn/Indeed/Glassdoor, and any other registered sources) "
        "across multiple locations and domains, deduplicates results, applies salary and experience filters, "
        "and stores matched jobs to the Fetched_Jobs sheet."
    ),
    verbose=False
)

mailer = Agent(
    role="Job Email Campaign Manager",
    goal="Build and send a personalised HTML job digest to each user, then update their email count",
    tools=[send_email_tool, sheets_update_cell_tool],
    backstory="Composes a styled HTML email from the filtered job list, sends it via SMTP, and increments the user's emails_sent counter in the Users sheet.",
    verbose=False
)

# ──────────────────────────────────────────────
# RESULT PARSER
# ──────────────────────────────────────────────

def parse_users_from_result(result) -> list:
    try:
        import ast
        text = str(result).strip()
        # Strip markdown fences if the LLM wrapped output
        if text.startswith('```json'): text = text[7:]
        if text.startswith('```python'): text = text[9:]
        if text.startswith('```'): text = text[3:]
        if text.endswith('```'): text = text[:-3]
        text = text.strip()

        try:
            users = json.loads(text)
        except:
            users = ast.literal_eval(text)

        if isinstance(users, list):
            return users
        return []
    except Exception as e:
        print(f"Failed to parse users: {e}")
        return []

# ──────────────────────────────────────────────
# CAMPAIGN RUNNER
# ──────────────────────────────────────────────

def run_campaign() -> dict:
    """Called by APScheduler. Orchestrates the full per-user loop."""

    # Step 1 — Load eligible users
    get_active_users_task = Task(
        description="""Read the Users sheet. Check system_enabled in System_Settings.
        Return a JSON list of user dictionary objects where status=='active'
        AND (has at least one non-empty location_1, location_2, location_3 OR remote_jobs=='true')
        AND domains is not empty. Do not include password_hash. Output MUST be valid JSON list ONLY.""",
        expected_output="JSON list of user dicts ready for job fetching.",
        agent=user_loader
    )

    loader_crew = Crew(
        agents=[user_loader],
        tasks=[get_active_users_task],
        process=Process.sequential,
        verbose=False
    )

    result = loader_crew.kickoff(inputs={})
    users = parse_users_from_result(result.raw)

    if not users:
        print("No active users. Exiting.")
        return {"sent": 0, "failed": 0, "no_jobs": 0}

    sent = failed = no_jobs = 0

    # Step 2 — Per-user loop (plain Python orchestration)
    fetch_task = Task(
        description="""For the given user in inputs['user'], parse domains by ';'.
        Build search_locations from location_1/2/3 plus 'India' if remote_jobs is true.
        For each domain×location pair, call JobSearchTool with what={domain}, where={location}, max_days_old=7,
        limit=ceil(daily_limit / n_domains). The tool automatically searches ALL available job sources
        (Adzuna, LinkedIn, Indeed, Glassdoor, etc.) and returns deduplicated results.
        Output MUST be a JSON list of raw deduplicated job dicts.""",
        expected_output="JSON list of raw deduplicated job dicts for this user.",
        agent=job_fetcher
    )

    filter_task = Task(
        description="""Apply filters to the raw job list:
        1. Salary: if min_salary > 0, exclude jobs where salary_max exists and salary_max < min_salary.
        2. Experience: if experience_level == 'senior', keep only jobs where title+description contains at least one of: ['senior','lead','principal','architect','5 years','5+ years']. If 'intermediate', exclude jobs that contain junior keywords: ['junior','entry','fresher','trainee'].
        3. Sort by created date descending.
        4. Slice to user's daily_limit.
        Output MUST be a JSON formatted list of filtered, sorted, sliced job dicts.""",
        expected_output="JSON list of filtered, sorted, sliced job dicts.",
        agent=job_fetcher
    )

    store_task = Task(
        description="""Append each job in the filtered list as a row to the Fetched_Jobs sheet with columns:
        timestamp, user_id, job_id, title, company, location, description, salary_min, salary_max,
        contract_type, created, redirect_url, matched_domain, source.
        Output the string 'Confirmation that jobs were stored.'""",
        expected_output="Confirmation that jobs were stored.",
        agent=job_fetcher
    )

    build_email_task = Task(
        description="""Using the filtered job list and user dict, build an HTML email string.
        Structure: gradient header with user first name and job count; one card per job showing title,
        domain badge, source badge (e.g. LinkedIn, Indeed, Adzuna), company, location,
        salary (formatted as Rs{n}L if >= 100000 else Rs{n:,}),
        description (max 300 chars), Apply Now button; footer with Dashboard and Unsubscribe links.
        Unsubscribe URL: {UNSUBSCRIBE_BASE_URL}?action=unsubscribe&user_id={user_id}.
        If filtered job list is empty, output 'no jobs'.
        Output the raw HTML string of the complete email.""",
        expected_output="Raw HTML string of the complete email or 'no jobs'.",
        agent=mailer
    )

    send_email_task = Task(
        description="""If the HTML output from BuildEmailTask is 'no jobs', output 'no jobs'.
        Otherwise, call SendEmailTool with: to=user.email, subject='🚀 {n} New Job Opportunities for You', html_body=<output of BuildEmailTask>.
        Output 'sent' or error string.""",
        expected_output="Confirmation 'sent', 'no jobs' or error string.",
        agent=mailer
    )

    update_count_task = Task(
        description="""If the previous task output was 'sent', call SheetsUpdateCellTool to increment the user's emails_sent counter in the Users sheet.
        Output 'Confirmation of counter update' or 'no update needed'.""",
        expected_output="Confirmation of counter update.",
        agent=mailer
    )

    for user in users:
        try:
            job_crew = Crew(
                agents=[job_fetcher, mailer],
                tasks=[fetch_task, filter_task, store_task, build_email_task, send_email_task, update_count_task],
                process=Process.sequential,
                verbose=False
            )
            result = job_crew.kickoff(inputs={"user": user})
            res_str = result.raw.lower()
            if "no jobs" in res_str:
                no_jobs += 1
            else:
                sent += 1
        except Exception as e:
            print(f"Failed for {user.get('email')}: {e}")
            failed += 1

        time.sleep(2)  # rate limit between users

    summary = {"sent": sent, "failed": failed, "no_jobs": no_jobs}
    print(f"Campaign complete: {summary}")
    return summary
