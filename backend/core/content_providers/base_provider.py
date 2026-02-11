#backend/core/content_providers/base_provider.py

from abc import ABC, abstractmethod


class BaseContentProvider(ABC):
    """
    Abstract provider interface for external syllabus/content sources.
    """

    @abstractmethod
    def connect(self):
        """Initialize connection to provider."""
        pass

    @abstractmethod
    def list_grades(self):
        """Return list of grade folders."""
        pass

    @abstractmethod
    def list_subjects(self, grade_folder_id):
        """Return subjects inside grade folder."""
        pass

    @abstractmethod
    def list_topics(self, subject_folder_id):
        """Return topics inside subject folder."""
        pass

    @abstractmethod
    def list_files(self, topic_folder_id):
        """Return files inside topic folder."""
        pass

    @abstractmethod
    def download_file(self, file_id):
        """Download file content."""
        pass