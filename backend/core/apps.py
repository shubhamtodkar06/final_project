# backend/core/apps.py
from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """
        Startup bootstrap tasks:
        1. One-time Google Drive syllabus sync (first run only)
        2. ChromaDB indexing
        """

        # Prevent double execution (important for dev server)
        if os.environ.get("RUN_MAIN") != "true":
            return

        # ----------------------------------
        # ⭐ One-time syllabus sync
        # ----------------------------------
        try:
            from student_notes.models import Standard

            if not Standard.objects.exists():
                logger.info("📥 No syllabus found. Running initial Google Drive sync...")
                from core.syllabus_sync_service import SyllabusSyncService
                svc = SyllabusSyncService()
                svc.sync_all()
                logger.info("✅ Initial syllabus sync completed.")
            else:
                logger.info("📘 Syllabus already present. Skipping Drive sync.")
        except Exception as e:
            logger.warning(f"⚠️ Syllabus auto-sync skipped or failed: {e}")

        # ----------------------------------
        # Re-index ChromaDB
        # ----------------------------------
        try:
            from core.chroma_indexer import reindex_all
            reindex_all()
            logger.info("✅ ChromaDB indexed successfully on startup.")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB indexing skipped or failed: {e}")