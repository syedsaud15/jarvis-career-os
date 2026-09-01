from __future__ import annotations

from typing import Any

MNC_COMPANIES = (
    "accenture", "amazon", "capco", "cognizant", "deloitte", "deutsche bank", "ey", "google",
    "ibm", "infosys", "microsoft", "oracle", "tcs", "wipro",
)
DATA_ENGINEERING_SKILLS = (
    "python", "sql", "spark", "pyspark", "airflow", "etl", "aws", "azure", "gcp", "databricks",
    "snowflake", "kafka", "dbt", "docker", "data warehouse",
)


def extract_skills(text: str) -> list[str]:
    normalized = text.lower()
    return [skill for skill in DATA_ENGINEERING_SKILLS if skill in normalized]


def rank_job(job: dict[str, Any], profile_skills: list[str] | None = None) -> dict[str, Any]:
    """Explainable, deterministic ranking for a Data Engineer career profile."""
    title = str(job.get("title") or "")
    company = str(job.get("company") or "")
    description = str(job.get("description") or "")
    haystack = f"{title} {description}".lower()
    inventory = profile_skills or list(DATA_ENGINEERING_SKILLS)
    matched_skills = [skill for skill in inventory if skill in haystack]
    job_skills = [skill for skill in DATA_ENGINEERING_SKILLS if skill in haystack]
    missing_skills = [skill for skill in job_skills if skill not in matched_skills]
    mnc_priority = any(company_name in company.lower() for company_name in MNC_COMPANIES)
    title_score = 20 if "data engineer" in title.lower() else 8 if "data" in title.lower() else 0
    skill_score = min(len(matched_skills) * 6, 48)
    company_score = 25 if mnc_priority else 0
    salary_score = 7 if job.get("salary_min") or job.get("salary_max") else 0
    job["match_score"] = min(title_score + skill_score + company_score + salary_score, 100)
    job["matched_skills"] = matched_skills
    job["missing_skills"] = missing_skills
    job["mnc_priority"] = mnc_priority
    reasons = []
    if "data engineer" in title.lower():
        reasons.append("The role title aligns with your Data Engineering target.")
    if matched_skills:
        reasons.append(f"Matched skills: {', '.join(matched_skills[:4])}.")
    if mnc_priority:
        reasons.append("Enterprise employer priority signal detected.")
    if not reasons:
        reasons.append("The listing is a nearby role signal; review the description before applying.")
    job["match_explanation"] = " ".join(reasons)
    job["next_step"] = (f"Strengthen {', '.join(missing_skills[:3])} with a targeted project before applying." if missing_skills else "Tailor your resume summary and apply while this role is active.")
    return job
