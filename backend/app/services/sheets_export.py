"""
Google Sheets export service.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.excel_export import TEMPLATES

logger = get_logger(__name__)
settings = get_settings()


class GoogleSheetsExportService:
    """Service for exporting extracted call data to Google Sheets."""

    def __init__(self):
        self._service = None

    def _get_service(self):
        """Lazy-load the Google Sheets API service."""
        if self._service is None:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Google service account file not found: {creds_path}. "
                    "Download from Google Cloud Console."
                )

            creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )
            self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def _get_drive_service(self):
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        return build("drive", "v3", credentials=creds)

    def create_spreadsheet(self, title: str, template_name: str = "customer_service_summary") -> str:
        """Create a new Google Spreadsheet and return its ID."""
        service = self._get_service()
        template = TEMPLATES.get(template_name, TEMPLATES["customer_service_summary"])

        spreadsheet = (
            service.spreadsheets()
            .create(body={"properties": {"title": title, "locale": "en_US"}})
            .execute()
        )
        spreadsheet_id = spreadsheet["spreadsheetId"]

        # Add headers
        headers = [col["header"] for col in template["columns"]]
        self.append_rows(spreadsheet_id, [headers], "A1")

        # Format header row
        self._format_header(spreadsheet_id, template)

        logger.info("sheets_created", spreadsheet_id=spreadsheet_id, title=title)
        return spreadsheet_id

    def append_rows(
        self,
        spreadsheet_id: str,
        values: List[List[Any]],
        range_name: str = "A1",
    ) -> dict:
        """Append rows to a Google Sheet."""
        service = self._get_service()
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body={"values": values},
            )
            .execute()
        )
        logger.info(
            "sheets_rows_appended",
            spreadsheet_id=spreadsheet_id,
            rows=len(values),
        )
        return result

    def export_data(
        self,
        spreadsheet_id: Optional[str],
        data_rows: List[Dict[str, Any]],
        template_name: str = "customer_service_summary",
    ) -> dict:
        """
        Export data rows to Google Sheets.
        Creates a new sheet if spreadsheet_id is None.
        Returns {spreadsheet_id, spreadsheet_url, rows_added}.
        """
        template = TEMPLATES.get(template_name, TEMPLATES["customer_service_summary"])
        columns = template["columns"]

        # Create new if needed
        if not spreadsheet_id:
            spreadsheet_id = self.create_spreadsheet(
                f"Call Export {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}",
                template_name,
            )

        # Transform data rows
        rows = []
        for data in data_rows:
            row = []
            for col in columns:
                value = self._extract_field(data, col["field"])
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                row.append(value if value is not None else "")
            rows.append(row)

        # Append
        self.append_rows(spreadsheet_id, rows, "A2")

        return {
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
            "rows_added": len(rows),
        }

    def share_spreadsheet(self, spreadsheet_id: str, email: str, role: str = "writer"):
        """Share a spreadsheet with a user."""
        drive = self._get_drive_service()
        drive.permissions().create(
            fileId=spreadsheet_id,
            body={"type": "user", "role": role, "emailAddress": email},
        ).execute()
        logger.info("sheets_shared", spreadsheet_id=spreadsheet_id, email=email)

    def _format_header(self, spreadsheet_id: str, template: dict):
        """Apply formatting to the header row."""
        service = self._get_service()
        bg_hex = template.get("header_bg", "366092")
        r, g, b = int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)

        requests = [
            {
                "repeatCell": {
                    "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": r / 255, "green": g / 255, "blue": b / 255},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                            "horizontalAlignment": "CENTER",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                }
            },
            {"updateSheetProperties": {
                "properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }},
        ]

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

    def _extract_field(self, obj: dict, path: str) -> Any:
        """Extract nested field value."""
        parts = path.split(".")
        current = obj
        for part in parts:
            if current is None:
                return ""
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return ""
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return ""
        return current if current is not None else ""
