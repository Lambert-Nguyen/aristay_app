
import json
import io
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from api.models import Task, TaskChecklist, ChecklistTemplate, ChecklistItem, ChecklistResponse, TaskImage, Property, Profile


@override_settings(MEDIA_ROOT='/tmp/test_media')
class TestUnifiedChecklistPhotos(TestCase):
    def setUp(self):
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
        self.template = ChecklistTemplate.objects.create(name='Tmpl', task_type='cleaning', is_active=True, created_by=self.user)
        self.item = ChecklistItem.objects.create(template=self.template, title='Take photo', item_type='photo_required')
        self.checklist = TaskChecklist.objects.create(task=self.task, template=self.template)
        self.response = ChecklistResponse.objects.create(checklist=self.checklist, item=self.item)

    def test_upload_creates_taskimage(self):
        # Use staff endpoint to upload checklist photo
        url = '/api/staff/checklist/photo/upload/'
        # Create a real JPEG image for testing
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        image_content = SimpleUploadedFile('test.jpg', img_bytes.getvalue(), content_type='image/jpeg')
        resp = self.client.post(url, {'item_id': str(self.response.id), 'photo': image_content})
        if resp.status_code != 200:
            print(f"Upload failed with status {resp.status_code}: {resp.content}")
        assert resp.status_code in (200, 302)
        # Verify TaskImage created and linked
        imgs = TaskImage.objects.filter(task=self.task, checklist_response=self.response, photo_type='checklist')
        assert imgs.count() == 1

    def test_remove_deletes_taskimage(self):
        # Seed a TaskImage
        # Create a real JPEG image for testing
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        seed_image = SimpleUploadedFile('seed.jpg', img_bytes.getvalue(), content_type='image/jpeg')
        ti = TaskImage.objects.create(task=self.task, checklist_response=self.response, image=seed_image, uploaded_by=self.user, photo_type='checklist')
        url = '/api/staff/checklist/photo/remove/'
        body = {'item_id': self.response.id, 'photo_url': ti.image.url}
        resp = self.client.post(url, data=json.dumps(body), content_type='application/json')
        assert resp.status_code == 200
        assert not TaskImage.objects.filter(id=ti.id).exists()
