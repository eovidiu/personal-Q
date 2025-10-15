"""
ABOUTME: Slack integration client with proper async/await support.
ABOUTME: Uses asyncio.to_thread, includes timeouts and retry logic for resilience.
"""

import asyncio
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


class SlackClient:
    """Slack API client wrapper with proper async support and resilience."""

    # Timeout for Slack API calls (seconds)
    TIMEOUT = 10.0

    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Slack client.

        Args:
            bot_token: Slack bot token
        """
        self.bot_token = bot_token
        self._client = None

    def set_token(self, bot_token: str):
        """Set or update bot token."""
        self.bot_token = bot_token
        self._client = None

    @property
    def client(self) -> WebClient:
        """Get Slack WebClient instance with timeout."""
        if not self.bot_token:
            raise ValueError("Slack bot token not configured")

        if self._client is None:
            self._client = WebClient(token=self.bot_token, timeout=self.TIMEOUT)

        return self._client

    @retry(
        retry=retry_if_exception_type(SlackApiError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def post_message(
        self, channel: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Post message to Slack channel (async).

        Args:
            channel: Channel ID or name
            text: Message text
            blocks: Optional rich message blocks

        Returns:
            Response from Slack API
        """
        try:
            # Run blocking Slack API call in executor to avoid blocking event loop
            response = await asyncio.to_thread(
                self.client.chat_postMessage, channel=channel, text=text, blocks=blocks
            )
            return {"success": True, "ts": response["ts"], "channel": response["channel"]}
        except SlackApiError as e:
            logger.error(f"Slack API error in post_message: {e.response['error']}")
            return {"success": False, "error": str(e.response["error"])}

    async def read_messages(
        self, channel: str, limit: int = 100, oldest: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Read messages from Slack channel (async).

        Args:
            channel: Channel ID
            limit: Maximum messages to retrieve
            oldest: Oldest message timestamp

        Returns:
            Messages from channel
        """
        try:
            # Run blocking call in executor
            response = await asyncio.to_thread(
                self.client.conversations_history, channel=channel, limit=limit, oldest=oldest
            )
            return {
                "success": True,
                "messages": response["messages"],
                "has_more": response.get("has_more", False),
            }
        except SlackApiError as e:
            logger.error(f"Slack API error in read_messages: {e.response['error']}")
            return {"success": False, "error": str(e.response["error"])}

    async def list_channels(self) -> Dict[str, Any]:
        """
        List available channels (async).

        Returns:
            List of channels
        """
        try:
            # Run blocking call in executor
            response = await asyncio.to_thread(self.client.conversations_list)
            return {
                "success": True,
                "channels": [
                    {"id": ch["id"], "name": ch["name"], "is_private": ch.get("is_private", False)}
                    for ch in response["channels"]
                ],
            }
        except SlackApiError as e:
            logger.error(f"Slack API error in list_channels: {e.response['error']}")
            return {"success": False, "error": str(e.response["error"])}

    async def react_to_message(self, channel: str, timestamp: str, emoji: str) -> Dict[str, Any]:
        """
        Add reaction to message (async).

        Args:
            channel: Channel ID
            timestamp: Message timestamp
            emoji: Emoji name (without colons)

        Returns:
            Response status
        """
        try:
            # Run blocking call in executor
            await asyncio.to_thread(
                self.client.reactions_add, channel=channel, timestamp=timestamp, name=emoji
            )
            return {"success": True}
        except SlackApiError as e:
            logger.error(f"Slack API error in react_to_message: {e.response['error']}")
            return {"success": False, "error": str(e.response["error"])}

    async def validate_token(self, token: str) -> bool:
        """
        Validate Slack bot token (async).

        Args:
            token: Token to validate

        Returns:
            True if valid
        """
        try:
            client = WebClient(token=token)
            # Run blocking call in executor
            await asyncio.to_thread(client.auth_test)
            return True
        except SlackApiError as e:
            logger.error(f"Slack token validation failed: {e}")
            return False


# Global client instance
slack_client = SlackClient()


def get_slack_client() -> SlackClient:
    """Get Slack client instance."""
    return slack_client
