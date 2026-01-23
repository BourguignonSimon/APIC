"""
Webhook Manager for notifying external systems of workflow events.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import aiohttp
except ImportError:
    aiohttp = None

from src.models.schemas import WebhookConfig, WebhookEvent

logger = logging.getLogger(__name__)


class WebhookManager:
    """Manager for webhook registrations and event notifications."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the webhook manager.

        Args:
            max_retries: Maximum number of delivery attempts
            retry_delay: Base delay between retries (exponential backoff)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.webhooks: Dict[str, List[WebhookConfig]] = {}

    async def register_webhook(
        self,
        project_id: str,
        config: Dict[str, Any]
    ) -> WebhookConfig:
        """
        Register a webhook for a project.

        Args:
            project_id: ID of the project
            config: Webhook configuration dict

        Returns:
            WebhookConfig object
        """
        webhook = WebhookConfig(
            project_id=project_id,
            url=config["url"],
            events=[WebhookEvent(e) if isinstance(e, str) else e for e in config["events"]],
            secret=config.get("secret"),
            active=config.get("active", True)
        )

        if project_id not in self.webhooks:
            self.webhooks[project_id] = []

        self.webhooks[project_id].append(webhook)
        logger.info(f"Registered webhook for project {project_id}: {webhook.url}")

        return webhook

    async def trigger_event(
        self,
        project_id: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Trigger an event and notify all registered webhooks.

        Args:
            project_id: ID of the project
            event_type: Type of event (e.g., "workflow.state_changed")
            data: Event data to send
        """
        if project_id not in self.webhooks:
            logger.debug(f"No webhooks registered for project {project_id}")
            return

        event = WebhookEvent(event_type) if isinstance(event_type, str) else event_type

        for webhook in self.webhooks[project_id]:
            if not webhook.active:
                continue

            if event not in webhook.events:
                continue

            # Deliver webhook asynchronously
            asyncio.create_task(
                self._deliver_webhook(webhook, event_type, data)
            )

    async def _deliver_webhook(
        self,
        webhook: WebhookConfig,
        event_type: str,
        data: Dict[str, Any],
        attempt: int = 1
    ) -> None:
        """
        Deliver a webhook payload with retry logic.

        Args:
            webhook: Webhook configuration
            event_type: Type of event
            data: Event data
            attempt: Current attempt number
        """
        if aiohttp is None:
            logger.warning("aiohttp not installed, skipping webhook delivery")
            return

        payload = {
            "event": event_type,
            "project_id": webhook.project_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Generate signature if secret is provided
        headers = {"Content-Type": "application/json"}
        if webhook.secret:
            signature = self.generate_signature(payload, webhook.secret)
            headers["X-Webhook-Signature"] = signature

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(
                            f"Webhook delivered successfully to {webhook.url} "
                            f"(event: {event_type}, attempt: {attempt})"
                        )
                        return
                    else:
                        logger.warning(
                            f"Webhook delivery failed with status {response.status}: {webhook.url}"
                        )
                        raise Exception(f"HTTP {response.status}")

        except Exception as e:
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.warning(
                    f"Webhook delivery failed (attempt {attempt}/{self.max_retries}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                await self._deliver_webhook(webhook, event_type, data, attempt + 1)
            else:
                logger.error(
                    f"Webhook delivery failed permanently after {self.max_retries} attempts: {e}"
                )

    def generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC signature for webhook payload.

        Args:
            payload: Payload dictionary
            secret: Secret key for HMAC

        Returns:
            Hex-encoded HMAC signature
        """
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Payload dictionary
            signature: Provided signature
            secret: Secret key for HMAC

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = self.generate_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)

    async def unregister_webhook(self, webhook_id: str, project_id: str) -> bool:
        """
        Unregister a webhook.

        Args:
            webhook_id: ID of the webhook to remove
            project_id: ID of the project

        Returns:
            True if webhook was removed, False if not found
        """
        if project_id not in self.webhooks:
            return False

        initial_count = len(self.webhooks[project_id])
        self.webhooks[project_id] = [
            w for w in self.webhooks[project_id]
            if w.id != webhook_id
        ]

        return len(self.webhooks[project_id]) < initial_count

    async def get_webhooks(self, project_id: str) -> List[WebhookConfig]:
        """
        Get all webhooks for a project.

        Args:
            project_id: ID of the project

        Returns:
            List of webhook configurations
        """
        return self.webhooks.get(project_id, [])
