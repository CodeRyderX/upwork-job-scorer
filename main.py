import os
import time
import requests
from fastapi import FastAPI
from supabase_client import supabase
from llm_client import score_job
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
ACTOR_ID = "XYTgO05GT5qAoSlxy"

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
def run_scraper():
    # 1. Trigger Apify actor
    run_response = requests.post(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs",
        headers={"Authorization": f"Bearer {APIFY_API_TOKEN}"},
        json={
            "clientHistory": ["noHires", "1to9Hires", "10+Hires"],
            "experienceLevel": ["intermediate", "expert"],
            "jobType": ["fixed", "hourly"],
            "maxJobAge": {"value": 2, "unit": "hours"},
            "page": 1,
            "pagesToScrape": 1,
            "paymentVerified": False,
            "perPage": 20,
            "query": "GoHighLevel",
            "sort": "newest"
        }
    )

    run_id = run_response.json()["data"]["id"]

    # 2. Wait for actor to finish
    while True:
        status_response = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            headers={"Authorization": f"Bearer {APIFY_API_TOKEN}"}
        )
        status = status_response.json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        elif status == "FAILED":
            return {"error": "Apify actor failed"}
        time.sleep(3)

    # 3. Fetch results
    dataset_id = status_response.json()["data"]["defaultDatasetId"]
    results_response = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        headers={"Authorization": f"Bearer {APIFY_API_TOKEN}"}
    )
    jobs = results_response.json()

    # 4. Score and store each job
    scored = []
    for job in jobs:
        title = job.get("title", "")
        description = job.get("description", "")
        url = job.get("url", "")
        budget = job.get("budget", "")
        posted_date = job.get("createdOn", "")

        try:
            result = score_job(title, description)
            supabase.table("jobs").insert({
                "title": title,
                "description": description,
                "budget": str(budget),
                "posted_date": str(posted_date),
                "job_url": url,
                "score": result["score"],
                "keywords_matched": result["keywords_matched"]
            }).execute()
            scored.append({**result, "title": title, "url": url})
        except Exception as e:
            print(f"Failed to score job: {title} — {e}")
            continue

    return {"jobs_processed": len(scored), "results": scored}

@app.get("/jobs")
def get_jobs():
    response = supabase.table("jobs").select("*").order("score", desc=True).execute()
    return response.data