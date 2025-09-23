
import json
import io
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient
from api.models import Task, TaskChecklist, ChecklistTemplate, ChecklistItem, ChecklistResponse, TaskImage, Property, Profile


@override_settings(MEDIA_ROOT='/tmp/test_media')
class TestUnifiedChecklistPhotos:
    def setup_method(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='tester', password='pass')
        Profile.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.login(username='tester', password='pass')
        # Create property and task
        self.property = Property.objects.create(name='Test Property')
        self.task = Task.objects.create(
            title='Clean Unit',
            task_type='cleaning',
            property_ref=self.property,
            created_by=self.user,
            assigned_to=self.user,
        )
        # Checklist with one photo-required item
        self.template = ChecklistTemplate.objects.create(name='Tmpl', task_type='cleaning', is_active=True)
        self.item = ChecklistItem.objects.create(template=self.template, title='Take photo', item_type='photo_required')
        self.checklist = TaskChecklist.objects.create(task=self.task, template=self.template)
        self.response = ChecklistResponse.objects.create(checklist=self.checklist, item=self.item)

    def test_upload_creates_taskimage(self, django_client):
        # Use staff endpoint to upload checklist photo
        url = '/api/staff/checklist/photo/upload/'
        image_content = SimpleUploadedFile('test.jpg', b'\xff\xd8\xff\xd9', content_type='image/jpeg')
        resp = django_client.post(url, {'item_id': str(self.response.id), 'photo': image_content})
        assert resp.status_code in (200, 302)
        # Verify TaskImage created and linked
        imgs = TaskImage.objects.filter(task=self.task, checklist_response=self.response, photo_type='checklist')
        assert imgs.count() == 1

    def test_remove_deletes_taskimage(self, django_client):
        # Seed a TaskImage
        ti = TaskImage.objects.create(task=self.task, checklist_response=self.response, image=SimpleUploadedFile('seed.jpg', b'\xff\xd8\xff\xd9', content_type='image/jpeg'), uploaded_by=self.user, photo_type='checklist')
        url = '/api/staff/checklist/photo/remove/'
        body = {'item_id': self.response.id, 'photo_url': ti.image.url}
        resp = django_client.post(url, data=json.dumps(body), content_type='application/json')
        assert resp.status_code == 200
        assert not TaskImage.objects.filter(id=ti.id).exists()
