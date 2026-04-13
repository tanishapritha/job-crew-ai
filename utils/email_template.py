from config import settings


def _format_source(source: str) -> str:
    """Convert raw source string to display-friendly name."""
    source_map = {
        "linkedin": "LinkedIn",
        "indeed": "Indeed",
        "glassdoor": "Glassdoor",
        "google": "Google Jobs",
        "adzuna": "Adzuna",
        "zip_recruiter": "ZipRecruiter",
        "naukri": "Naukri",
    }
    return source_map.get(source.lower().strip(), source.title())


def create_job_email_html(user: dict, jobs: list) -> str:
    """Build a styled HTML email for job opportunities."""
    first_name = user.get('name', 'User').split(' ')[0]
    n_jobs = len(jobs)

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
            .content {{ padding: 20px; }}
            .job-card {{ border: 1px solid #e2e8f0; border-radius: 6px; padding: 15px; margin-bottom: 15px; }}
            .job-title {{ font-size: 18px; font-weight: 600; color: #2d3748; margin: 0 0 8px 0; }}
            .badges {{ margin-bottom: 10px; }}
            .badge {{ display: inline-block; padding: 3px 8px; background: #edf2f7; color: #4a5568; font-size: 12px; border-radius: 4px; margin-right: 6px; font-weight: 500; }}
            .badge-source {{ background: #ebf4ff; color: #3182ce; }}
            .company-loc {{ font-size: 14px; color: #718096; margin-bottom: 10px; }}
            .salary {{ font-weight: 600; color: #38a169; font-size: 15px; margin-bottom: 10px; }}
            .desc {{ font-size: 14px; color: #4a5568; line-height: 1.5; margin-bottom: 15px; }}
            .apply-btn {{ display: inline-block; background: #4299e1; color: white; text-decoration: none; padding: 8px 16px; border-radius: 4px; font-size: 14px; font-weight: 500; }}
            .footer {{ background: #f7fafc; padding: 20px; text-align: center; font-size: 12px; color: #a0aec0; border-top: 1px solid #e2e8f0; }}
            .footer a {{ color: #4299e1; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Hi {first_name}, here are {n_jobs} new job opportunities! 🚀</h1>
            </div>
            <div class="content">
    """

    for job in jobs:
        title = job.get('title', 'Job Title')
        domain = job.get('matched_domain', 'Job')
        source_raw = job.get('source', 'unknown')
        source_display = _format_source(source_raw)
        company = job.get('company', 'Unknown Company')
        location = job.get('location', 'Remote')
        desc = job.get('description', '')[:300] + ('...' if len(job.get('description', '')) > 300 else '')
        url = job.get('redirect_url', '#')

        salary_min = float(job.get('salary_min') or 0)
        salary_max = float(job.get('salary_max') or 0)
        salary_str = "Salary Undisclosed"

        if salary_min > 0 or salary_max > 0:
            avg_salary = (salary_min + salary_max) / 2 if salary_min and salary_max else (salary_max or salary_min)
            if avg_salary >= 100000:
                salary_str = f"₹{avg_salary/100000:.1f}L"
            else:
                salary_str = f"₹{avg_salary:,.0f}"

        html += f"""
                <div class="job-card">
                    <h2 class="job-title">{title}</h2>
                    <div class="badges">
                        <span class="badge">{domain}</span>
                        <span class="badge badge-source">📌 {source_display}</span>
                    </div>
                    <div class="company-loc">🏢 {company} &nbsp; 📍 {location}</div>
                    <div class="salary">💰 {salary_str}</div>
                    <div class="desc">{desc}</div>
                    <a href="{url}" class="apply-btn">Apply on {source_display} →</a>
                </div>
        """

    unsubscribe_link = f"{settings.UNSUBSCRIBE_BASE_URL}/unsubscribe?user_id={user.get('user_id')}"

    html += f"""
            </div>
            <div class="footer">
                <p>You received this email because you subscribed to job alerts.</p>
                <p>
                    <a href="{settings.DASHBOARD_URL}">📊 Open Dashboard</a> |
                    <a href="{unsubscribe_link}">Unsubscribe</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html
