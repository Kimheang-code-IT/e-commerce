import logging
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Table styling (Google Sheets API RGB 0–1)
_HEADER_BG = {"red": 0.12, "green": 0.31, "blue": 0.47}
_HEADER_FG = {"red": 1.0, "green": 1.0, "blue": 1.0}
_BAND_A = {"red": 0.95, "green": 0.97, "blue": 1.0}
_BAND_B = {"red": 1.0, "green": 1.0, "blue": 1.0}


class GoogleSheetService:
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self._creds = None

    def _service(self):
        return build("sheets", "v4", credentials=self._get_credentials(), cache_discovery=False)

    def _get_credentials(self):
        if not self._creds:
            self._creds = service_account.Credentials.from_service_account_file(
                settings.google_service_account_file, scopes=self.scopes
            )
        return self._creds

    def _spreadsheet_id(self) -> str:
        sheet_id = (settings.google_sheet_id or "").strip()
        if not sheet_id:
            raise ValueError("GOOGLE_SHEET_ID is not configured")
        return sheet_id

    def _execute(self, request, *, retries: int = 4):
        """Run a Sheets API request; retry on HTTP 429 (rate limit)."""
        delays = (0, 20, 40, 60)
        last_exc: Exception | None = None
        for attempt in range(min(retries, len(delays))):
            if attempt > 0:
                time.sleep(delays[attempt])
            try:
                return request.execute()
            except HttpError as exc:
                last_exc = exc
                if exc.resp.status == 429 and attempt < retries - 1:
                    logger.warning(
                        "Google Sheets rate limit (429), retry %s/%s",
                        attempt + 1,
                        retries - 1,
                    )
                    continue
                raise
        if last_exc:
            raise last_exc
        return request.execute()

    def _resolve_sheet_id(self, service, sheet_name: str) -> int:
        spreadsheet = self._execute(
            service.spreadsheets().get(spreadsheetId=self._spreadsheet_id())
        )
        for sheet in spreadsheet.get("sheets", []):
            props = sheet.get("properties") or {}
            if props.get("title") == sheet_name:
                return int(props["sheetId"])
        body = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        resp = self._execute(
            service.spreadsheets().batchUpdate(
                spreadsheetId=self._spreadsheet_id(), body=body
            )
        )
        return int(resp["replies"][0]["addSheet"]["properties"]["sheetId"])

    def ensure_tab(self, sheet_name: str) -> int:
        service = self._service()
        return self._resolve_sheet_id(service, sheet_name)

    def ensure_tab_and_headers(self, sheet_name: str, headers: list[str]):
        """Legacy: ensure tab exists and header row when sheet is empty."""
        service = self._service()
        self._resolve_sheet_id(service, sheet_name)
        result = self._execute(
            service.spreadsheets().values().get(
                spreadsheetId=self._spreadsheet_id(), range=f"'{sheet_name}'!A1:Z1"
            )
        )
        if not result.get("values"):
            self._execute(
                service.spreadsheets().values().update(
                    spreadsheetId=self._spreadsheet_id(),
                    range=f"'{sheet_name}'!A1",
                    valueInputOption="RAW",
                    body={"values": [headers]},
                )
            )

    def _clear_existing_table_decorations(self, sheet_id: int) -> None:
        """Remove banding and filters so re-sync can re-apply styling."""
        service = self._service()
        spreadsheet = self._execute(
            service.spreadsheets().get(
                spreadsheetId=self._spreadsheet_id(),
                fields="sheets(properties.sheetId,bandedRanges,filterViews,basicFilter)",
            )
        )
        requests = []
        for sheet in spreadsheet.get("sheets", []):
            props = sheet.get("properties") or {}
            if props.get("sheetId") != sheet_id:
                continue
            for banded in sheet.get("bandedRanges", []):
                band_id = banded.get("bandedRangeId")
                if band_id is not None:
                    requests.append({"deleteBanding": {"bandedRangeId": band_id}})
            if sheet.get("basicFilter"):
                requests.append({"clearBasicFilter": {"sheetId": sheet_id}})
            break
        if requests:
            self._execute(
                service.spreadsheets().batchUpdate(
                    spreadsheetId=self._spreadsheet_id(), body={"requests": requests}
                )
            )

    def _apply_table_format(self, sheet_id: int, num_cols: int, num_rows: int) -> None:
        if num_cols < 1 or num_rows < 1:
            return
        service = self._service()
        self._clear_existing_table_decorations(sheet_id)
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": _HEADER_BG,
                            "textFormat": {"bold": True, "foregroundColor": _HEADER_FG},
                            "horizontalAlignment": "CENTER",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount",
                }
            },
            {
                "setBasicFilter": {
                    "filter": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": num_rows,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols,
                        }
                    }
                }
            },
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": num_cols,
                    }
                }
            },
        ]
        if num_rows > 1:
            requests.append(
                {
                    "addBanding": {
                        "bandedRange": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": num_rows,
                                "startColumnIndex": 0,
                                "endColumnIndex": num_cols,
                            },
                            "rowProperties": {
                                "headerColor": _HEADER_BG,
                                "firstBandColor": _BAND_A,
                                "secondBandColor": _BAND_B,
                            },
                        }
                    }
                }
            )
        self._execute(
            service.spreadsheets().batchUpdate(
                spreadsheetId=self._spreadsheet_id(), body={"requests": requests}
            )
        )

    def sync_full_table(self, sheet_name: str, headers: list[str], rows: list[list]) -> int:
        """
        Replace tab content with headers + all data rows and apply table styling
        (frozen header, filter, banded rows, column auto-width).
        """
        service = self._service()
        sheet_id = self._resolve_sheet_id(service, sheet_name)
        self._execute(
            service.spreadsheets().values().clear(
                spreadsheetId=self._spreadsheet_id(),
                range=f"'{sheet_name}'",
            )
        )

        values = [headers] + rows
        num_cols = max(len(headers), max((len(r) for r in rows), default=0))
        padded = []
        for row in values:
            cells = list(row)
            if len(cells) < num_cols:
                cells.extend([""] * (num_cols - len(cells)))
            padded.append(cells[:num_cols])

        self._execute(
            service.spreadsheets().values().update(
                spreadsheetId=self._spreadsheet_id(),
                range=f"'{sheet_name}'!A1",
                valueInputOption="RAW",
                body={"values": padded},
            )
        )

        self._apply_table_format(sheet_id, num_cols, len(padded))
        logger.info("Synced %s rows to tab %s", len(rows), sheet_name)
        return len(rows)

    def append_rows(self, sheet_name: str, rows: list[list]):
        if not rows:
            return
        service = self._service()
        body = {"values": rows}
        return self._execute(
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self._spreadsheet_id(),
                range=f"'{sheet_name}'!A1",
                valueInputOption="RAW",
                body=body,
            )
        )

    def get_existing_first_column_values(self, sheet_name: str) -> set[str]:
        service = self._service()
        result = self._execute(
            service.spreadsheets()
            .values()
            .get(spreadsheetId=self._spreadsheet_id(), range=f"'{sheet_name}'!A2:A")
        )
        values = result.get("values", [])
        return {str(row[0]).strip() for row in values if row and str(row[0]).strip()}

    def append_unique_rows_by_first_column(self, sheet_name: str, rows: list[list]) -> int:
        if not rows:
            return 0
        existing_ids = self.get_existing_first_column_values(sheet_name)
        filtered: list[list] = []
        for row in rows:
            if not row:
                continue
            row_id = str(row[0]).strip()
            if not row_id or row_id in existing_ids:
                continue
            filtered.append(row)
            existing_ids.add(row_id)
        if not filtered:
            return 0
        self.append_rows(sheet_name, filtered)
        return len(filtered)


google_sheet_service = GoogleSheetService()
