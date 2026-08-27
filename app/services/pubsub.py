import asyncio
import logging
from typing import Dict, Any, Callable, List
from app.config import get_settings

logger = logging.getLogger("civicfix.pubsub")
settings = get_settings()


class PubSubService:
    """Pub/Sub service supporting live GCP Pub/Sub or local async event queue."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self.use_live_pubsub = False

        if not settings.MOCK_PUBSUB and settings.GOOGLE_CLOUD_PROJECT:
            try:
                from google.cloud import pubsub_v1
                self.publisher = pubsub_v1.PublisherClient()
                self.use_live_pubsub = True
                logger.info("Connected to Google Cloud Pub/Sub.")
            except Exception as e:
                logger.warning(f"Could not connect to live Pub/Sub: {e}. Falling back to internal async bus.")
        else:
            logger.info("Running internal asynchronous event bus (MOCK_PUBSUB=True).")

    async def publish_event(self, topic: str, payload: Dict[str, Any]):
        """Publish an asynchronous workflow event."""
        logger.info(f"[PubSub] Event published to topic '{topic}': {payload.get('action', 'EVENT')}")
        handlers = self._subscribers.get(topic, [])
        for handler in handlers:
            asyncio.create_task(handler(payload))

    def subscribe(self, topic: str, callback: Callable):
        """Register a subscriber callback for a specific topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)


pubsub_service = PubSubService()
