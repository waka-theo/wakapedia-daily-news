import os
import json
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_drive_service():
    """
    Get Google Drive service using service account credentials.

    Requires GOOGLE_SERVICE_ACCOUNT_JSON environment variable with the
    service account JSON content, or a service_account.json file in the project root.
    """
    # Try environment variable first (for GitHub Actions)
    sa_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

    if sa_json:
        sa_info = json.loads(sa_json)
        credentials = service_account.Credentials.from_service_account_info(
            sa_info, scopes=SCOPES
        )
    else:
        # Try local file
        sa_file = Path(__file__).parent.parent.parent / 'service_account.json'
        if sa_file.exists():
            credentials = service_account.Credentials.from_service_account_file(
                str(sa_file), scopes=SCOPES
            )
        else:
            raise FileNotFoundError(
                "Google Service Account credentials not found. "
                "Set GOOGLE_SERVICE_ACCOUNT_JSON env var or create service_account.json"
            )

    return build('drive', 'v3', credentials=credentials)


def upload_pdf_to_drive(pdf_path: str, folder_id: str = None) -> str:
    """
    Upload a PDF to Google Drive and return the shareable link.

    Args:
        pdf_path: Path to the PDF file
        folder_id: Optional Google Drive folder ID to upload to

    Returns:
        Shareable link to the PDF
    """
    service = get_drive_service()

    file_metadata = {
        'name': Path(pdf_path).name,
        'mimeType': 'application/pdf'
    }

    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(pdf_path, mimetype='application/pdf')

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    # Make the file publicly accessible (anyone with the link can view)
    service.permissions().create(
        fileId=file['id'],
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    return file.get('webViewLink')


def upload_and_get_link(pdf_path: str) -> str:
    """
    Upload PDF to Google Drive and return the link.
    Returns None if upload fails.
    """
    try:
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        link = upload_pdf_to_drive(pdf_path, folder_id)
        print(f"PDF uploaded to Google Drive: {link}")
        return link
    except Exception as e:
        print(f"Failed to upload to Google Drive: {e}")
        return None
