from django.db import migrations


def seed_academic_data(apps, schema_editor):
    Standard = apps.get_model("student_notes", "Standard")
    Subject = apps.get_model("student_notes", "Subject")
    Topic = apps.get_model("student_notes", "Topic")

    # ---- Standards ----
    for grade in range(5, 13):
        Standard.objects.get_or_create(grade=grade)

    # ---- Subjects per standard ----
    subjects = ["Mathematics", "Science", "English"]

    for standard in Standard.objects.all():
        for subject_name in subjects:
            subject, _ = Subject.objects.get_or_create(
                name=subject_name,
                standard=standard
            )

            # ---- Topics per subject ----
            if subject_name == "Mathematics":
                topics = ["Fractions", "Algebra", "Geometry"]
            elif subject_name == "Science":
                topics = ["Physics Basics", "Chemistry Basics"]
            else:
                topics = ["Grammar", "Comprehension"]

            for idx, topic_name in enumerate(topics):
                Topic.objects.get_or_create(
                    name=topic_name,
                    subject=subject,
                    defaults={"order_index": idx}
                )


class Migration(migrations.Migration):

    dependencies = [
        ("student_notes", "0002_ainote_masternote_standard_subject_topic_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_academic_data),
    ]