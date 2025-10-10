"""
Slack integration client.
"""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict, Any, Optional


class SlackClient:
    """Slack API client wrapper."""

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
        """Get Slack WebClient instance."""
        if not self.bot_token:
            raise ValueError("Slack bot token not configured")

        if self._client is None:
            self._client = WebClient(token=self.bot_token)

        return self._client

    async def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Post message to Slack channel.

        Args:
            channel: Channel ID or name
            text: Message text
            blocks: Optional rich message blocks

        Returns:
            Response from Slack API
        """
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            return {
                "success": True,
                "ts": response["ts"],
                "channel": response["channel"]
            }
        except SlackApiError as e:
            return {
                "success": False,
                "error": str(e.response["error"])
            }

    async def read_messages(
        self,
        channel: str,
        limit: int = 100,
        oldest: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Read messages from Slack channel.

        Args:
            channel: Channel ID
            limit: Maximum messages to retrieve
            oldest: Oldest message timestamp

        Returns:
            Messages from channel
        """
        try:
            response = self.client.conversations_history(
                channel=channel,
                limit=limit,
                oldest=oldest
            )
            return {
                "success": True,
                "messages": response["messages"],
                "has_more": response.get("has_more", False)
            }
        except SlackApiError as e:
            return {
                "success": False,
                "error": str(e.response["error"])
            }

    async def list_channels(self) -> Dict[str, Any]:
        """
        List available channels.

        Returns:
            List of channels
        """
        try:
            response = self.client.conversations_list()
            return {
                "success": True,
                "channels": [
                    {
                        "id": ch["id"],
                        "name": ch["name"],
                        "is_private": ch.get("is_private", False)
                    }
                    for ch in response["channels"]
                ]
            }
        except SlackApiError as e:
            return {
                "success": False,
                "error": str(e.response["error"])
            }

    async def react_to_message(
        self,
        channel: str,
        timestamp: str,
        emoji: str
    ) -> Dict[str, Any]:
        """
        Add reaction to message.

        Args:
            channel: Channel ID
            timestamp: Message timestamp
            emoji: Emoji name (without colons)

        Returns:
            Response status
        """
        try:
            self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
            return {"success": True}
        except SlackApiError as e:
            return {
                "success": False,
                "error": str(e.response["error"])
            }

    async def validate_token(self, token: str) -> bool:
        """
        Validate Slack bot token.

        Args:
            token: Token to validate

        Returns:
            True if valid
        """
        try:
            client = WebClient(token=token)
            client.auth_test()
            return True
        except SlackApiError:
            return False


# Global client instance
slack_client = SlackClient()


def get_slack_client() -> SlackClient:
    """Get Slack client instance."""
    return slack_client
