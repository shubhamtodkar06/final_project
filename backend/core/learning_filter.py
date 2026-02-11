# backend/core/learning_filter.py

class LearningFilters:

    def __init__(
        self,
        grade=None,
        subjects=None,
        topics=None,
        weak_only=False,
        strong_only=False,
        unlocked_only=False,
        revision_due=False,
    ):
        self.grade = grade
        self.subjects = subjects or []
        self.topics = topics or []
        self.weak_only = weak_only
        self.strong_only = strong_only
        self.unlocked_only = unlocked_only
        self.revision_due = revision_due