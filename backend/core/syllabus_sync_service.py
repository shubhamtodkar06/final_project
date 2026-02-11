# backend/core/syllabus_sync_service.py
import logging
from django.contrib.auth import get_user_model
from student_notes.models import Standard, Subject, Topic
from resources.utils import ingest_resource
from core.chroma_indexer import reindex_all
from .content_providers.google_drive_provider import GoogleDriveProvider

logger = logging.getLogger(__name__)
User = get_user_model()


class SyllabusSyncService:

    def __init__(self):
        self.provider = GoogleDriveProvider()
        self.provider.connect()
        self.system_user = User.objects.filter(is_superuser=True).first()

    # ----------------------------------
    # MAIN SYNC FUNCTION
    # ----------------------------------
    def sync_all(self):

        grades = self.provider.list_grades()

        for grade in grades:
            standard = Standard.objects.get_or_create(
                grade=grade["grade"]
            )[0]

            subjects = self.provider.list_subjects(grade["id"])

            for subj in subjects:

                subject = Subject.objects.get_or_create(
                    name=subj["name"],
                    standard=standard
                )[0]

                topics = self.provider.list_topics(subj["id"])

                for index, topic_folder in enumerate(topics):

                    topic = Topic.objects.get_or_create(
                        name=topic_folder["name"],
                        subject=subject,
                        defaults={"order_index": index}
                    )[0]

                    self._sync_resources(
                        standard,
                        subject,
                        topic,
                        topic_folder["id"]
                    )

        reindex_all()
        logger.info("✅ Syllabus + Resources Sync Completed")

    # ----------------------------------
    # RESOURCE SYNC
    # ----------------------------------
    def _sync_resources(self, standard, subject, topic, topic_folder_id):

        files = self.provider.list_files(topic_folder_id)

        for f in files:
            try:
                file_data = self.provider.download_file(f["id"])

                ingest_resource(
                    user=self.system_user,
                    title=f["name"],
                    content="Imported from Google Drive",
                    subject=subject.name,
                    grade_level=standard.grade,
                    type="system"
                )

            except Exception as e:
                logger.error(f"❌ Failed syncing file {f['name']} → {e}")