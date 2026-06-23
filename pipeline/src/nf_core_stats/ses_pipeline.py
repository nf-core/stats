"""DLT pipeline for collecting AWS SES newsletter list statistics.

The nf-core monthly newsletter (https://github.com/nf-core/newsletter) uses
Amazon SES list management as its contact store. A contact is a *subscriber*
once it is opted in to the ``monthly-newsletter`` topic (double opt-in); before
confirming it sits on the list opted out, and a global unsubscribe sets
``UnsubscribeAll``.

This pipeline snapshots those counts once per run so we can chart newsletter
sign-ups over time alongside the other community stats.

Authentication:
- Uses boto3, which reads standard AWS credentials from the environment
  (``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY``, or an assumed role via
  OIDC in GitHub Actions).
- The credentials need ``ses:ListContacts`` on the ``nf-core-newsletter``
  contact list, which lives in ``eu-west-1``.
"""

from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

import boto3
import dlt

from ._logging import log_pipeline_stats, logger

# Mirrors nf-core/newsletter src/nf_core_newsletter/config.py defaults.
AWS_REGION = "eu-west-1"
CONTACT_LIST_NAME = "nf-core-newsletter"
TOPIC_NAME = "monthly-newsletter"

# SES topic subscription status the newsletter service sets on opt-in.
OPT_IN = "OPT_IN"

# Max page size accepted by the SES v2 ListContacts API.
SES_PAGE_SIZE = 1000


def _is_subscribed(contact: dict[str, Any]) -> bool:
    """True if the contact is opted in to the newsletter topic and not globally unsubscribed.

    Matches the logic in nf-core/newsletter ``ses.is_subscribed``.
    """
    if contact.get("UnsubscribeAll"):
        return False
    for pref in contact.get("TopicPreferences", []):
        if pref.get("TopicName") == TOPIC_NAME:
            return pref.get("SubscriptionStatus") == OPT_IN
    return False


def _iter_all_contacts(client: Any) -> Iterator[dict[str, Any]]:
    """Yield every contact on the list (no filter), paginating as needed.

    ``ListContacts`` returns ``TopicPreferences`` and ``UnsubscribeAll`` on each
    contact, so we can classify subscribed / pending / unsubscribed without a
    per-contact ``GetContact`` call.
    """
    next_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"ContactListName": CONTACT_LIST_NAME, "PageSize": SES_PAGE_SIZE}
        if next_token:
            kwargs["NextToken"] = next_token
        response = client.list_contacts(**kwargs)
        yield from response.get("Contacts", [])
        next_token = response.get("NextToken")
        if not next_token:
            return


@dlt.source(name="ses")
def ses_source() -> list[Any]:
    """DLT source for AWS SES newsletter list statistics."""
    client = boto3.client("sesv2", region_name=AWS_REGION)
    return [ses_stats_resource(client)]


@dlt.resource(name="newsletter_stats", write_disposition="merge", primary_key=["timestamp"])
def ses_stats_resource(client: Any) -> Iterator[dict[str, Any]]:
    """Snapshot the newsletter contact list: subscribed, pending and unsubscribed counts."""
    total = 0
    subscribed = 0
    unsubscribed = 0

    for contact in _iter_all_contacts(client):
        total += 1
        if contact.get("UnsubscribeAll"):
            unsubscribed += 1
        elif _is_subscribed(contact):
            subscribed += 1

    # On the list but neither confirmed nor globally unsubscribed (double opt-in pending).
    pending = total - subscribed - unsubscribed

    logger.info(
        f"SES list '{CONTACT_LIST_NAME}': {total} contacts "
        f"({subscribed} subscribed, {pending} pending, {unsubscribed} unsubscribed)"
    )

    yield {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "total_contacts": total,
        "subscribed": subscribed,
        "pending": pending,
        "unsubscribed": unsubscribed,
    }


def main(*, destination="motherduck"):
    """
    Run the AWS SES newsletter data ingestion pipeline

    Args:
        destination: dlt backend. Use 'motherduck' for production. Can use 'duckdb' for local testing
    """
    logger.info("Starting AWS SES newsletter data pipeline...")

    pipeline = dlt.pipeline(
        pipeline_name="ses_stats",
        destination=destination,
        dataset_name="ses",
    )

    load_info = pipeline.run(ses_source())
    log_pipeline_stats(pipeline, load_info)

    logger.info("AWS SES newsletter data pipeline completed successfully!")
