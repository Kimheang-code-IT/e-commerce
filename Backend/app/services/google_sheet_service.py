import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from app.core.config import settings

logger = logging.getLogger(__name__)

class GoogleSheetService:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self._creds = None

    def _get_credentials(self):
        if not self._creds:
            try:
                self._creds = service_account.Credentials.from_service_account_file(
                    settings.google_service_account_file, scopes=self.scopes
                )
            except Exception as e:
                logger.error(f"Failed to load Google service account credentials: {e}")
                raise
        return self._creds

    def ensure_tab_and_headers(self, sheet_name: str, headers: list[str]):
        """Ensure the tab exists and has headers if empty."""
        try:
            service = build('sheets', 'v4', credentials=self._get_credentials(), cache_discovery=False)
            spreadsheet = service.spreadsheets().get(spreadsheetId=settings.google_sheet_id).execute()
            
            sheet_exists = any(s['properties']['title'] == sheet_name for s in spreadsheet['sheets'])
            
            if not sheet_exists:
                # Create sheet
                body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {'title': sheet_name}
                        }
                    }]
                }
                service.spreadsheets().batchUpdate(spreadsheetId=settings.google_sheet_id, body=body).execute()
                logger.info(f"Created new tab: {sheet_name}")

            # Check if headers exist (read first row)
            result = service.spreadsheets().values().get(
                spreadsheetId=settings.google_sheet_id,
                range=f"'{sheet_name}'!A1:Z1"
            ).execute()
            
            if not result.get('values'):
                # Write headers
                body = {'values': [headers]}
                service.spreadsheets().values().update(
                    spreadsheetId=settings.google_sheet_id,
                    range=f"'{sheet_name}'!A1",
                    valueInputOption="RAW",
                    body=body
                ).execute()
                logger.info(f"Initialized headers for: {sheet_name}")
        except Exception as e:
            logger.error(f"Failed to ensure tab and headers for {sheet_name}: {e}")
            raise

    def append_rows(self, sheet_name: str, rows: list[list]):
        """Append rows to a specific tab."""
        if not rows:
            return
        
        try:
            service = build('sheets', 'v4', credentials=self._get_credentials(), cache_discovery=False)
            body = {'values': rows}
            
            return service.spreadsheets().values().append(
                spreadsheetId=settings.google_sheet_id,
                range=f"'{sheet_name}'!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
        except Exception as e:
            logger.error(f"Failed to append rows to {sheet_name}: {e}")
            raise

google_sheet_service = GoogleSheetService()
