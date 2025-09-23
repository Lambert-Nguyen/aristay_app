from django.db import migrations


def backfill_checklist_photos(apps, schema_editor):
    TaskImage = apps.get_model('api', 'TaskImage')
    ChecklistPhoto = apps.get_model('api', 'ChecklistPhoto')
    ChecklistResponse = apps.get_model('api', 'ChecklistResponse')

    # Iterate all ChecklistPhoto and create TaskImage if not already present
    for cp in ChecklistPhoto.objects.all().select_related('response', 'uploaded_by'):
        response = cp.response
        checklist = getattr(response, 'checklist', None)
        task = getattr(checklist, 'task', None)
        if not task:
            continue

        # Check if a TaskImage already references this file for this task and response
        exists = TaskImage.objects.filter(
            task_id=task.id,
            checklist_response_id=response.id,
            image=cp.image.name,
        ).exists()
        if exists:
            continue

        # Determine next sequence number for 'checklist' type within the task
        next_seq = TaskImage.objects.filter(task_id=task.id, photo_type='checklist').count() + 1

        TaskImage.objects.create(
            task_id=task.id,
            image=cp.image,  # reuse file reference
            uploaded_by_id=getattr(cp.uploaded_by, 'id', None),
            photo_type='checklist',
            sequence_number=next_seq,
            checklist_response_id=response.id,
            photo_status='approved',  # existing photos considered approved
            description=cp.caption or '',
        )


def noop_reverse(apps, schema_editor):
    # We do not delete TaskImage records when reversing; keep data safe
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0069_booking_booking_no_overlap_active'),
    ]

    operations = [
        migrations.RunPython(backfill_checklist_photos, reverse_code=noop_reverse),
    ]


