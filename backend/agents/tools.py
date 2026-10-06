import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_core.tools import tool

from retrival.engine import get_rag_response 
from job_search.job_search_service import fetch_jobs, get_job_detail_by_id, format_job_short, format_job_short_with_days_left
from helpers.utils import get_datetime_local


@tool
def search_guidelines(question: str) -> str:
    """Search the IT Departments thesis guidelines (Uppsala University) and return an
    answer. Use for deadlines, project plan, programme requirements,
    roles, presentation, publishing and other thesis rules."""

    return get_rag_response(question)


@tool
def search_jobtech(topic: str, location: str = "") -> str:
    """Search live thesis (exjobb) positions in Sweden from the JobTech API.
    topic: subject area, e.g. "machine learning" or "data science".
    location: optional city, e.g. "Stockholm".
    Returns open thesis positions with id, title, employer, location and link.
    Use get_job_details for the description and deadline of one position,
    and check_deadlines to see which positions close soonest."""

    try:
        jobs = fetch_jobs(topic, location or None)
    except Exception as e:
        print(f"Job search failed: {e}")
        return "The job search is temporarily unavailable. Please try again shortly."
    if not jobs:
        return "No open thesis positions found for this search. A broader topic or another city may give more results."
    
    return "\n".join(format_job_short(job) for job in jobs)


@tool
def get_job_details(job_id: str) -> str:
    """Get the full details of one thesis position: description, deadline and link.
    Use when the student asks about a specific position from the search results."""
    try:
        job = get_job_detail_by_id(job_id)
    except Exception as e:
        print(f"Job lookup failed: {e}")
        return "The job details are temporarily unavailable. Please try again shortly."

    if not job:
        return "This position could not be found. It may have been removed."

    cities = ", ".join(job.cities) or "not stated"
    deadline = job.deadline_at.strftime("%Y-%m-%d") if job.deadline_at else "not stated"
    return (
        f"title: {job.headline}\nemployer: {job.employer}\nlocation: {cities}\n"
        f"deadline: {deadline}\nlink: {job.url}\n\n"
        f"description:\n{job.description[:2000]}"
    )


@tool
def check_deadlines(job_ids: list[str], within_days: int | None = None) -> str:
    """Calculate how many days are left to apply for thesis positions found by search_jobtech,
    sorted by urgency (soonest deadline first).
    job_ids: ids from the search results.
    within_days: optional, only include positions closing within this many days (e.g. 2 or 7)."""

    now = get_datetime_local()
    rows = []
    for job_id in job_ids:
        
        try:
            job = get_job_detail_by_id(job_id)
        except Exception as e:
            print(f"Job lookup failed for {job_id}: {e}")
            continue

        if not job or not job.deadline_at or job.deadline_at < now:
            continue
        days = (job.deadline_at - now).days
        if within_days is None or days <= within_days:
            rows.append((days, job))

    if not rows:
        return "None of these positions close within that time frame."

    rows.sort(key=lambda row: row[0])
    return "\n".join(
        format_job_short_with_days_left(job, days)
        for days, job in rows
    )