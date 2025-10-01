from django.db import migrations


def backfill_checklist_photos(apps, schema_editor):
    TaskImage = apps.get_model('api', 'TaskImage')
    ChecklistPhoto = apps.get_model('api', 'ChecklistPhoto')
    ChecklistResponse = apps.get_model('api', 'ChecklistResponse')

    for cp in ChecklistPhoto.objects.all().select_related('response', 'uploaded_by'):
        response = cp.response
        checklist = getattr(response, 'checklist', None)
        task = getattr(checklist, 'task', None)
        if not task:
            continue

        exists = TaskImage.objects.filter(
            task_id=task.id,
            checklist_response_id=response.id,
            image=cp.image.name,
        ).exists()
        if exists:
            continue

        next_seq = TaskImage.objects.filter(task_id=task.id, photo_type='checklist').count() + 1

        TaskImage.objects.create(
            task_id=task.id,
            image=cp.image,
            uploaded_by_id=getattr(cp.uploaded_by, 'id', None),
            photo_type='checklist',
            sequence_number=next_seq,
            checklist_response_id=response.id,
            photo_status='approved',
            description=cp.caption or '',
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0075_booking_booking_no_overlap_active'),
    ]

    operations = [
        migrations.RunPython(backfill_checklist_photos, reverse_code=noop_reverse),
    ]


