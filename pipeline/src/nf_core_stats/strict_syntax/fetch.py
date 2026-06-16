import httpx

from .._logging import logger
from .paths import PIPELINES_URL


def fetch_pipelines() -> list[dict]:
    """Fetch active nf-core pipelines from nf-co.re."""
    logger.info("Fetching pipelines from %s", PIPELINES_URL)
    response = httpx.get(PIPELINES_URL, timeout=60)
    response.raise_for_status()
    data = response.json()

    pipelines = []
    for pipeline in data.get("remote_workflows", []):
        if pipeline.get("archived", False):
            continue
        pipelines.append(
            {
                "name": pipeline["name"],
                "full_name": pipeline["full_name"],
                "html_url": f"https://github.com/{pipeline['full_name']}",
            }
        )

    logger.info("Found %d active pipelines", len(pipelines))
    return pipelines
