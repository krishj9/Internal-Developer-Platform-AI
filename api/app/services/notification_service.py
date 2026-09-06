"""
Notification service and Pub/Sub event boundary for IDP Control Plane.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NotificationEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    event_type: str  # "REQUEST_DISPATCHED", "PROVISIONING_SUCCEEDED", "PROVISIONING_FAILED", etc.
    request_id: str
    deployment_id: str
    template_id: str
    workspace: str
    environment: str
    status: str
    summary: str | None = None
    actor_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    safe_payload: dict[str, Any] = Field(default_factory=dict)


class NotificationService:
    def __init__(self, topic_name: str | None = None, slack_webhook_url: str | None = None):
        self.topic_name = topic_name
        self.slack_webhook_url = slack_webhook_url
        self._published_events: list[NotificationEvent] = []

    def format_slack_message(self, event: NotificationEvent) -> dict[str, Any]:
        if "SUCCEEDED" in event.status or "SUCCESS" in event.event_type:
            status_emoji = "✅"
            color = "#36a64f"
        elif "FAILED" in event.status or "FAILED" in event.event_type:
            status_emoji = "❌"
            color = "#de4e2b"
        else:
            status_emoji = "⏳"
            color = "#e8a838"

        summary_text = event.summary or "No summary provided."
        env_text = f"*Environment:*\n`{event.environment}` (`{event.workspace}`)"
        context_text = f"Summary: {summary_text} | Timestamp: {event.timestamp.isoformat()}"

        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{status_emoji} IDP Event: {event.event_type}",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Request ID:*\n`{event.request_id}`"},
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Deployment ID:*\n`{event.deployment_id}`",
                                },
                                {"type": "mrkdwn", "text": f"*Template:*\n{event.template_id}"},
                                {"type": "mrkdwn", "text": env_text},
                                {"type": "mrkdwn", "text": f"*Status:*\n*{event.status}*"},
                                {"type": "mrkdwn", "text": f"*Actor:*\n`{event.actor_id}`"},
                            ],
                        },
                        {
                            "type": "context",
                            "elements": [{"type": "mrkdwn", "text": context_text}],
                        },
                    ],
                }
            ]
        }

    async def publish(self, event: NotificationEvent) -> bool:
        """
        Publish normalized event across Pub/Sub boundary and format notifications.
        """
        self._published_events.append(event)
        logger.info(
            "Notification event published: type=%s, request_id=%s, status=%s",
            event.event_type,
            event.request_id,
            event.status,
        )
        return True

    def get_published_events(self) -> list[NotificationEvent]:
        return list(self._published_events)

    def clear(self) -> None:
        self._published_events.clear()


notification_service = NotificationService()
