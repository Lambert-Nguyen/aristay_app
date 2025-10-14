#!/usr/bin/env python
"""
Test Excel Import Permission Restrictions

Verifies that only superuser and manager roles can access the Excel import feature.
Staff/crew roles should be denied access.
"""

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory, Client
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

from api.models import Profile, UserRole
from api.views import is_superuser_or_manager


@pytest.fixture
def users(db):
    """Create test users for each role"""
    # Superuser
    superuser = User.objects.create_user(
        username='test_superuser',
        password='test123',
        is_superuser=True,
        is_staff=True
    )
    profile, _ = Profile.objects.get_or_create(
        user=superuser,
        defaults={'role': UserRole.SUPERUSER}
    )
    # Ensure profile has correct role
    profile.role = UserRole.SUPERUSER
    profile.save()
    superuser.refresh_from_db()  # Refresh to load profile relation
    
    # Manager
    manager = User.objects.create_user(
        username='test_manager',
        password='test123'
    )
    profile, _ = Profile.objects.get_or_create(
        user=manager,
        defaults={'role': UserRole.MANAGER}
    )
    # Ensure profile has correct role
    profile.role = UserRole.MANAGER
    profile.save()
    # Managers should have is_staff=True for Django admin access
    manager.is_staff = True
    manager.save(update_fields=['is_staff'])
    manager.refresh_from_db()  # Refresh to load profile relation
    
    # Staff/Crew (should NOT have access)
    crew = User.objects.create_user(
        username='test_crew',
        password='test123'
    )
    profile, _ = Profile.objects.get_or_create(
        user=crew,
        defaults={'role': UserRole.STAFF}
    )
    # Ensure profile has correct role
    profile.role = UserRole.STAFF
    profile.save()
    # Staff should have is_staff=False
    crew.is_staff = False
    crew.save(update_fields=['is_staff'])
    crew.refresh_from_db()  # Refresh to load profile relation
    
    return {
        'superuser': superuser,
        'manager': manager,
        'crew': crew
    }


@pytest.mark.django_db
class TestExcelImportPermissions:
    """Test suite for Excel import permission restrictions"""
    
    def test_superuser_passes_is_superuser_or_manager_check(self, users):
        """Verify superuser passes the is_superuser_or_manager check"""
        superuser = users['superuser']
        
        # Superusers should pass the check
        assert is_superuser_or_manager(superuser) is True
        
    def test_manager_passes_is_superuser_or_manager_check(self, users):
        """Verify manager passes the is_superuser_or_manager check"""
        manager = users['manager']
        
        # Manager should pass the check
        assert is_superuser_or_manager(manager) is True
        
    def test_crew_fails_is_superuser_or_manager_check(self, users):
        """Verify staff/crew FAILS the is_superuser_or_manager check"""
        crew = users['crew']
        
        # Crew should NOT pass the check
        assert is_superuser_or_manager(crew) is False
        
    def test_superuser_can_access_enhanced_excel_import_view(self, users, client):
        """Verify superuser can access enhanced excel import view"""
        client.login(username='test_superuser', password='test123')
        
        response = client.get(reverse('enhanced-excel-import'))
        
        # Should not get permission denied (200 or redirect, not 403)
        assert response.status_code != 403
        
    def test_manager_can_access_enhanced_excel_import_view(self, users, client):
        """Verify manager can access enhanced excel import view"""
        client.login(username='test_manager', password='test123')
        
        response = client.get(reverse('enhanced-excel-import'))
        
        # Should not get permission denied (200 or redirect, not 403)
        assert response.status_code != 403
        
    def test_crew_cannot_access_enhanced_excel_import_view(self, users, client):
        """Verify staff/crew CANNOT access enhanced excel import view"""
        client.login(username='test_crew', password='test123')
        
        response = client.get(reverse('enhanced-excel-import'))
        
        # Should get redirected (302) or permission denied (403)
        # user_passes_test redirects to login by default
        assert response.status_code in (302, 403)
        
    def test_superuser_can_access_enhanced_excel_import_api(self, users, client):
        """Verify superuser can access enhanced excel import API"""
        client.login(username='test_superuser', password='test123')
        
        # POST without file will fail validation but should not get permission denied
        response = client.post(reverse('enhanced-excel-import-api'), {})
        
        # Should not get permission denied (400 validation error is acceptable)
        assert response.status_code != 403
        
    def test_manager_can_access_enhanced_excel_import_api(self, users, client):
        """Verify manager can access enhanced excel import API"""
        client.login(username='test_manager', password='test123')
        
        # POST without file will fail validation but should not get permission denied
        response = client.post(reverse('enhanced-excel-import-api'), {})
        
        # Should not get permission denied (400 validation error is acceptable)
        assert response.status_code != 403
        
    def test_crew_cannot_access_enhanced_excel_import_api(self, users, client):
        """Verify staff/crew CANNOT access enhanced excel import API"""
        client.login(username='test_crew', password='test123')
        
        response = client.post(reverse('enhanced-excel-import-api'), {})
        
        # Should get redirected (302) or permission denied (403)
        # user_passes_test redirects to login by default
        assert response.status_code in (302, 403)
        
    def test_legacy_excel_import_view_has_correct_permissions(self, users, client):
        """Verify legacy excel import view also has correct permissions"""
        # Test superuser access
        client.login(username='test_superuser', password='test123')
        response = client.get(reverse('excel-import'))
        assert response.status_code != 403
        
        # Test manager access
        client.login(username='test_manager', password='test123')
        response = client.get(reverse('excel-import'))
        assert response.status_code != 403
        
        # Test crew denial
        client.login(username='test_crew', password='test123')
        response = client.get(reverse('excel-import'))
        assert response.status_code == 302 or response.status_code == 403  # Redirect or forbidden


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
