import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from job_search.job_fetcher import get_jobs, get_job
from dto.job_ad import JobAd
from helpers.constants import (
    THESIS_TERMS, 
    JOBTECH_SENDER_LIMIT, 
    JOBTECH_REQUEST_LIMIT,
    JOBTECH_SORT_ORDER_RELEVANT,
    JOBTECH_SORT_ORDER_NEWEST,
    JOBTECH_SORT_ORDERS,
    JOBTECH_SORT_PARAMS
)
from helpers.utils import get_datetime_local, clean_text, parse_datetime_isoformat, days_ago

from typing import Optional


JOB_CACHE: dict[str, JobAd] = {}


def normalize(ad: dict) -> Optional[JobAd]:
    if ad and ad.get("id"):
        return JobAd(
            id = ad.get("id") or "",
            headline = clean_text(ad.get("headline") or ""),
            employer = clean_text((ad.get("employer") or {}).get("name") or ""),
            cities = [
                addr["municipality"]
                for addr in ad.get("workplace_addresses") or []
                if addr.get("municipality")
            ],
            deadline_at = parse_datetime_isoformat(ad.get("application_deadline")) or get_datetime_local(),
            posted_at = parse_datetime_isoformat(ad.get("publication_date")) or get_datetime_local(),
            description = clean_text((ad.get("description") or {}).get("text") or ""),
            url = ad.get("webpage_url") or ""
        )

    return None


def is_thesis_ad(title: str, desc: str) -> bool:
    title = title.lower()
    desc = desc.lower()

    if any(emp_type in title for emp_type in THESIS_TERMS):
        return True

    return False


def is_job_application_open(application_deadline) -> bool:
    if not application_deadline:
        return False
    
    return parse_datetime_isoformat(application_deadline) >= get_datetime_local()


def is_valid_ad(ad: dict) -> bool:
    deadline = ad.get("application_deadline")
    title = clean_text(ad.get("headline") or "")
    desc = clean_text((ad.get("description") or {}).get("text") or "")
    
    if not desc or not is_job_application_open(deadline):
        return False

    if not is_thesis_ad(title=title, desc=desc):
        #print(f"Non thesis: {title}, url: {ad.get('webpage_url')}")
        return False

    return True


def fetch_jobs(topic: str, 
               location: str | None = None,
               sort: JOBTECH_SORT_ORDERS = JOBTECH_SORT_ORDER_RELEVANT,
               published_after_days: Optional[int] = None,
               published_before_days: Optional[int] = None) -> list[JobAd]:
    
    found: dict[str, JobAd] = {}

    base_params = {"sort": JOBTECH_SORT_PARAMS[sort], "limit": JOBTECH_REQUEST_LIMIT}
    if published_after_days is not None:
        base_params["published-after"] = days_ago(published_after_days)
    if published_before_days is not None:
        base_params["published-before"] = days_ago(published_before_days)

    for term in THESIS_TERMS:
        query = " ".join(
            part
            for part in (topic, location, term)
            if part
        )
        params = {**base_params, "q": query}
        hits = get_jobs(params=params)
        #print(f"{query}: total {len(hits)} job ads")

        for ad in hits:
            job = normalize(ad)
            if job and is_valid_ad(ad):
                found[job.id] = job

    results = list(found.values())

    results.sort(key=lambda job: job.posted_at, reverse=True)
    
    jobs = results[:JOBTECH_SENDER_LIMIT]
    JOB_CACHE.update({job.id: job for job in jobs})
    return jobs



def get_job_detail_by_id(job_id: str) -> JobAd | None:
    if job_id in JOB_CACHE:
        return JOB_CACHE[job_id]
    ad = get_job(job_id)

    if ad:
        job = normalize(ad)

        if job and job.id:
            JOB_CACHE[job_id] = job
            return job

    return None


def format_job_short(job: JobAd) -> str:
    cities = ", ".join(job.cities) or "not stated"
    return f"- id: {job.id} | {job.headline} | {job.employer} | {cities} | {job.posted_at} | {job.url}"

def format_job_short_with_days_left(job: JobAd, days: int) -> str:
    return f"- {job.headline} ({job.employer}): {days} days left, deadline {job.deadline_at:%Y-%m-%d} | {job.url}"