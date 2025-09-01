from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime, date, timedelta
from django.utils import timezone
import io
import pandas as pd

from api.models import Property, Booking, Profile, UserRole
from api.services.excel_import_service import ExcelImportService
from .base import BaseTestCase


class ExcelImportServiceTest(BaseTestCase):
    """Test Excel import service functionality"""
    
    def setUp(self):
        super().setUp()
        # Excel service requires a user and optional template
        self.excel_import_service = ExcelImportService(user=self.admin_user)
    
    def test_excel_service_initialization(self):
        """Test that ExcelImportService initializes correctly"""
        service = ExcelImportService(user=self.admin_user)
        self.assertIsNotNone(service)
        self.assertEqual(service.user, self.admin_user)

    def test_excel_service_requires_user(self):
        """Test that ExcelImportService requires a user"""
        with self.assertRaises(TypeError):
            ExcelImportService()  # Should fail without user parameter
            
    def test_service_has_import_method(self):
        """Test that the service has the expected import method"""
        self.assertTrue(hasattr(self.excel_import_service, 'import_excel_file'))
        self.assertTrue(callable(getattr(self.excel_import_service, 'import_excel_file')))
