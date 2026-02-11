#backend/core/content_providers/google_drive_provider.py

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from .base_provider import BaseContentProvider


class GoogleDriveProvider(BaseContentProvider):

    def __init__(self):
        self.service = None
        self.root_folder_id = os.getenv("DRIVE_ROOT_FOLDER_ID")

    # ----------------------------------
    # CONNECT
    # ----------------------------------
    def connect(self):
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )

        self.service = build("drive", "v3", credentials=credentials)

    # ----------------------------------
    # Helper
    # ----------------------------------
    def _list_items(self, parent_id):
        query = f"'{parent_id}' in parents and trashed=false"

        results = self.service.files().list(
            q=query,
            fields="files(id, name, mimeType)"
        ).execute()

        return results.get("files", [])

    # ----------------------------------
    # Grades
    # ----------------------------------
    def list_grades(self):
        folders = self._list_items(self.root_folder_id)
        grades = []

        for f in folders:
            if "Grade" in f["name"]:
                grades.append({
                    "id": f["id"],
                    "name": f["name"],
                    "grade": int(f["name"].split()[-1])
                })

        return grades

    # ----------------------------------
    # Subjects
    # ----------------------------------
    def list_subjects(self, grade_folder_id):
        return self._list_items(grade_folder_id)

    # ----------------------------------
    # Topics
    # ----------------------------------
    def list_topics(self, subject_folder_id):
        return self._list_items(subject_folder_id)

    # ----------------------------------
    # Files
    # ----------------------------------
    def list_files(self, topic_folder_id):
        return self._list_items(topic_folder_id)

    # ----------------------------------
    # Download
    # ----------------------------------
    def download_file(self, file_id):
        request = self.service.files().get_media(fileId=file_id)
        return request.execute()
# backend/core/content_providers/google_drive_provider.py

import os
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from .base_provider import BaseContentProvider


class GoogleDriveProvider(BaseContentProvider):
    """
    Google Drive content provider.

    ✔ Portable credential loading (works on any machine)
    ✔ Uses DRIVE_ROOT_FOLDER_ID from .env
    ✔ Read-only access
    """

    def __init__(self):
        self.service = None
        self.root_folder_id = os.getenv("DRIVE_ROOT_FOLDER_ID")

        if not self.root_folder_id:
            raise ValueError("DRIVE_ROOT_FOLDER_ID is not set in .env")

    # ----------------------------------
    # CONNECT
    # ----------------------------------
    def connect(self):
        """
        Connect to Google Drive using service account credentials.
        Resolves credential path dynamically using BASE_DIR.
        """

        cred_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

        if not cred_file:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE is not set in .env")

        # Resolve relative path safely (project-root based)
        if not os.path.isabs(cred_file):
            cred_file = os.path.join(settings.BASE_DIR.parent, cred_file)

        if not os.path.exists(cred_file):
            raise FileNotFoundError(
                f"Google service account file not found at: {cred_file}"
            )

        credentials = service_account.Credentials.from_service_account_file(
            cred_file,
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )

        self.service = build("drive", "v3", credentials=credentials)

    # ----------------------------------
    # Internal Helper
    # ----------------------------------
    def _list_items(self, parent_id):
        """
        List non-trashed files/folders inside a parent folder.
        """
        query = f"'{parent_id}' in parents and trashed=false"

        results = self.service.files().list(
            q=query,
            fields="files(id, name, mimeType)"
        ).execute()

        return results.get("files", [])

    # ----------------------------------
    # Grades (Top-level folders)
    # Expected format: Grade 5, Grade 6, ...
    # ----------------------------------
    def list_grades(self):
        folders = self._list_items(self.root_folder_id)
        grades = []

        for f in folders:
            if f["mimeType"] == "application/vnd.google-apps.folder" and "Grade" in f["name"]:
                try:
                    grade_number = int(f["name"].split()[-1])
                except ValueError:
                    continue

                grades.append({
                    "id": f["id"],
                    "name": f["name"],
                    "grade": grade_number
                })

        return grades

    # ----------------------------------
    # Subjects (Folders under Grade)
    # ----------------------------------
    def list_subjects(self, grade_folder_id):
        return [
            f for f in self._list_items(grade_folder_id)
            if f["mimeType"] == "application/vnd.google-apps.folder"
        ]

    # ----------------------------------
    # Topics (Folders under Subject)
    # ----------------------------------
    def list_topics(self, subject_folder_id):
        return [
            f for f in self._list_items(subject_folder_id)
            if f["mimeType"] == "application/vnd.google-apps.folder"
        ]

    # ----------------------------------
    # Files (Inside Topic folder)
    # ----------------------------------
    def list_files(self, topic_folder_id):
        return [
            f for f in self._list_items(topic_folder_id)
            if f["mimeType"] != "application/vnd.google-apps.folder"
        ]

    # ----------------------------------
    # Download file content (binary)
    # ----------------------------------
    def download_file(self, file_id):
        request = self.service.files().get_media(fileId=file_id)
        return request.execute()