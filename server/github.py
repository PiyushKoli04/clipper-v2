"""GitHub Actions workflow_dispatch trigger helper."""

import os
import httpx
from worker.utils import log


async def trigger_workflow(job_id: str) -> dict:
    """Trigger the GitHub Actions clipper.yml workflow via workflow_dispatch."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")  # format: "owner/repo"

    if not token or not repo:
        log.warning("GITHUB_TOKEN or GITHUB_REPO not configured. Skipping workflow_dispatch.")
        return {
            "triggered": False,
            "message": "GITHUB_TOKEN or GITHUB_REPO not configured on server",
        }

    url = f"https://api.github.com/repos/{repo}/actions/workflows/clipper.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "ref": "main",
        "inputs": {
            "job_id": job_id,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=15.0)

        if response.status_code == 204:
            log.info("Successfully dispatched workflow for job %s on repo %s", job_id, repo)
            return {"triggered": True, "message": "Workflow dispatched"}
        else:
            log.error("Failed to dispatch workflow: %d %s", response.status_code, response.text)
            return {
                "triggered": False,
                "status_code": response.status_code,
                "message": response.text,
            }

