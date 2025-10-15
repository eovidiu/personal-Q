"""
Microsoft Graph API client for Outlook and OneDrive.
"""

from msgraph import GraphServiceClient
from azure.identity import DeviceCodeCredential, ClientSecretCredential
from typing import List, Dict, Any, Optional


class MicrosoftGraphClient:
    """Microsoft Graph API client wrapper."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize Microsoft Graph client.

        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self._client = None

    def set_credentials(self, client_id: str, client_secret: str, tenant_id: str):
        """Set or update credentials."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self._client = None

    @property
    def client(self) -> GraphServiceClient:
        """Get Graph client instance."""
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise ValueError("Microsoft Graph credentials not configured")

        if self._client is None:
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id, client_id=self.client_id, client_secret=self.client_secret
            )
            self._client = GraphServiceClient(credentials=credential)

        return self._client

    # Outlook/Email methods
    async def read_emails(
        self, folder: str = "inbox", limit: int = 10, unread_only: bool = False
    ) -> Dict[str, Any]:
        """
        Read emails from mailbox.

        Args:
            folder: Mail folder (inbox, sent, drafts)
            limit: Maximum emails to retrieve
            unread_only: Filter for unread emails only

        Returns:
            List of emails
        """
        try:
            query_params = {"$top": limit, "$orderby": "receivedDateTime DESC"}

            if unread_only:
                query_params["$filter"] = "isRead eq false"

            messages = await self.client.me.messages.get(query_params)

            return {
                "success": True,
                "emails": [
                    {
                        "id": msg.id,
                        "subject": msg.subject,
                        "from": (
                            msg.from_address.email_address.address if msg.from_address else None
                        ),
                        "body": msg.body.content if msg.body else "",
                        "received": msg.received_date_time,
                        "is_read": msg.is_read,
                    }
                    for msg in messages.value
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_email(
        self, to: str, subject: str, body: str, body_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Send email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            body_type: "text" or "html"

        Returns:
            Send status
        """
        try:
            message = {
                "subject": subject,
                "body": {"contentType": body_type, "content": body},
                "toRecipients": [{"emailAddress": {"address": to}}],
            }

            await self.client.me.send_mail(message)

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Calendar methods
    async def get_calendar_events(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get calendar events.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            List of calendar events
        """
        try:
            query_params = {"$orderby": "start/dateTime"}

            if start_date and end_date:
                query_params["$filter"] = (
                    f"start/dateTime ge '{start_date}' and end/dateTime le '{end_date}'"
                )

            events = await self.client.me.calendar.events.get(query_params)

            return {
                "success": True,
                "events": [
                    {
                        "id": event.id,
                        "subject": event.subject,
                        "start": event.start.date_time if event.start else None,
                        "end": event.end.date_time if event.end else None,
                        "location": event.location.display_name if event.location else None,
                    }
                    for event in events.value
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_calendar_event(
        self, subject: str, start: str, end: str, body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create calendar event.

        Args:
            subject: Event subject
            start: Start time (ISO format)
            end: End time (ISO format)
            body: Event description

        Returns:
            Created event details
        """
        try:
            event = {
                "subject": subject,
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end": {"dateTime": end, "timeZone": "UTC"},
                "body": {"contentType": "text", "content": body or ""},
            }

            created = await self.client.me.calendar.events.post(event)

            return {"success": True, "event_id": created.id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # OneDrive methods
    async def list_files(self, folder_path: str = "root") -> Dict[str, Any]:
        """
        List files in OneDrive folder.

        Args:
            folder_path: Folder path (default: root)

        Returns:
            List of files
        """
        try:
            if folder_path == "root":
                items = await self.client.me.drive.root.children.get()
            else:
                items = await self.client.me.drive.root.item_with_path(folder_path).children.get()

            return {
                "success": True,
                "files": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "size": item.size,
                        "modified": item.last_modified_date_time,
                        "is_folder": item.folder is not None,
                    }
                    for item in items.value
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read file content from OneDrive.

        Args:
            file_path: File path

        Returns:
            File content
        """
        try:
            content = await self.client.me.drive.root.item_with_path(file_path).content.get()

            return {"success": True, "content": content.decode("utf-8")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write file to OneDrive.

        Args:
            file_path: File path
            content: File content

        Returns:
            Write status
        """
        try:
            await self.client.me.drive.root.item_with_path(file_path).content.put(
                content.encode("utf-8")
            )

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def validate_credentials(
        self, client_id: str, client_secret: str, tenant_id: str
    ) -> bool:
        """
        Validate Microsoft Graph credentials.

        Args:
            client_id: Client ID
            client_secret: Client secret
            tenant_id: Tenant ID

        Returns:
            True if valid
        """
        try:
            credential = ClientSecretCredential(
                tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
            )
            client = GraphServiceClient(credentials=credential)
            await client.me.get()
            return True
        except Exception:
            return False


# Global client instance
graph_client = MicrosoftGraphClient()


def get_graph_client() -> MicrosoftGraphClient:
    """Get Microsoft Graph client instance."""
    return graph_client
