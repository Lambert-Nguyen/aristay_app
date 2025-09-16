"""
Tests for the invite code system and user registration
"""
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from api.models import InviteCode, Profile
from api.registration_views import generate_invite_code
from api.serializers import InviteCodeValidationSerializer, UserRegistrationSerializer


@pytest.mark.django_db
class TestInviteCodeModel:
    """Test InviteCode model functionality"""
    
    def test_create_invite_code(self):
        """Test creating an invite code"""
        user = User.objects.create_user(username='admin', password='testpass')
        invite = InviteCode.objects.create(
            code='TEST123',
            created_by=user,
            task_group='cleaning',
            role='member',
            max_uses=1
        )
        
        assert invite.code == 'TEST123'
        assert invite.created_by == user
        assert invite.task_group == 'cleaning'
        assert invite.role == 'member'
        assert invite.max_uses == 1
        assert invite.used_count == 0
        assert invite.is_active is True
        assert invite.is_expired is False
        assert invite.is_usable is True
    
    def test_invite_code_expiration(self):
        """Test invite code expiration logic"""
        user = User.objects.create_user(username='admin', password='testpass')
        
        # Non-expiring code
        invite1 = InviteCode.objects.create(
            code='NEVER123',
            created_by=user,
            expires_at=None
        )
        assert invite1.is_expired is False
        
        # Expired code
        invite2 = InviteCode.objects.create(
            code='EXPIRED123',
            created_by=user,
            expires_at=timezone.now() - timedelta(days=1)
        )
        assert invite2.is_expired is True
        
        # Future expiration
        invite3 = InviteCode.objects.create(
            code='FUTURE123',
            created_by=user,
            expires_at=timezone.now() + timedelta(days=1)
        )
        assert invite3.is_expired is False
    
    def test_invite_code_usage_tracking(self):
        """Test invite code usage tracking"""
        user = User.objects.create_user(username='admin', password='testpass')
        invite = InviteCode.objects.create(
            code='USAGE123',
            created_by=user,
            max_uses=2
        )
        
        # Initially usable
        assert invite.is_usable is True
        assert invite.used_count == 0
        
        # Use code once
        user1 = User.objects.create_user(username='user1', password='testpass')
        invite.use_code(user1)
        assert invite.used_count == 1
        assert invite.is_usable is True
        assert user1 in invite.used_by.all()
        
        # Use code again
        user2 = User.objects.create_user(username='user2', password='testpass')
        invite.use_code(user2)
        assert invite.used_count == 2
        assert invite.is_usable is False  # Reached max uses
    
    def test_invite_code_cannot_be_reused_single_use(self):
        """Test that single-use codes cannot be reused by the same user"""
        user = User.objects.create_user(username='admin', password='testpass')
        invite = InviteCode.objects.create(
            code='SINGLE123',
            created_by=user,
            max_uses=1
        )
        
        user1 = User.objects.create_user(username='user1', password='testpass')
        invite.use_code(user1)
        
        # Same user cannot use again
        assert not invite.can_be_used_by(user1)
        
        # Different user can use (if max_uses > 1)
        user2 = User.objects.create_user(username='user2', password='testpass')
        assert not invite.can_be_used_by(user2)  # But max_uses is 1, so no
    
    def test_invite_code_inactive(self):
        """Test inactive invite codes"""
        user = User.objects.create_user(username='admin', password='testpass')
        invite = InviteCode.objects.create(
            code='INACTIVE123',
            created_by=user,
            is_active=False
        )
        
        assert invite.is_usable is False
        assert not invite.can_be_used_by(user)


@pytest.mark.django_db
class TestInviteCodeGeneration:
    """Test invite code generation"""
    
    def test_generate_invite_code_format(self):
        """Test that generated codes have correct format"""
        code = generate_invite_code()
        assert len(code) == 8
        assert code.isalnum()
        assert code.isupper()
    
    def test_generate_invite_code_uniqueness(self):
        """Test that generated codes are unique"""
        codes = set()
        for _ in range(100):
            code = generate_invite_code()
            assert code not in codes
            codes.add(code)


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration with invite codes"""
    
    def test_registration_with_valid_invite_code(self):
        """Test successful user registration with valid invite code"""
        admin_user = User.objects.create_user(username='admin', password='testpass')
        invite = InviteCode.objects.create(
            code='REG123',
            created_by=admin_user,
            task_group='cleaning',
            role='member',
            max_uses=1
        )
        
        # Create user via registration
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123',
            first_name='New',
            last_name='User'
        )
        
        # Create profile with invite code settings
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = invite.role
        profile.task_group = invite.task_group
        profile.save()
        
        # Mark invite code as used
        invite.use_code(user)
        
        assert user.username == 'newuser'
        assert profile.role == 'member'
        assert profile.task_group == 'cleaning'
        assert invite.used_count == 1
        assert user in invite.used_by.all()
    
    def test_registration_serializer_validation(self):
        """Test registration serializer validation"""
        # Valid data
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'invite_code': 'TEST123'
        }
        
        serializer = UserRegistrationSerializer(data=valid_data)
        assert serializer.is_valid()
        
        # Invalid data - passwords don't match
        invalid_data = valid_data.copy()
        invalid_data['password_confirm'] = 'different'
        
        serializer = UserRegistrationSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
    
    def test_invite_code_validation_serializer(self):
        """Test invite code validation serializer"""
        # Valid code
        valid_data = {'code': 'TEST123'}
        serializer = InviteCodeValidationSerializer(data=valid_data)
        assert serializer.is_valid()
        
        # Invalid code - too long
        invalid_data = {'code': 'A' * 33}
        serializer = InviteCodeValidationSerializer(data=invalid_data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestInviteCodeAPI:
    """Test invite code API endpoints"""
    
    def test_validate_invite_code_api_valid(self, client):
        """Test validating a valid invite code via API"""
        admin_user = User.objects.create_user(username='admin', password='testpass')
        invite = InviteCode.objects.create(
            code='API123',
            created_by=admin_user,
            task_group='maintenance',
            role='manager',
            max_uses=5
        )
        
        response = client.post('/api/validate-invite/', {
            'code': 'API123'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['role'] == 'manager'
        assert data['task_group'] == 'maintenance'
        assert data['max_uses'] == 5
        assert data['used_count'] == 0
    
    def test_validate_invite_code_api_invalid(self, client):
        """Test validating an invalid invite code via API"""
        response = client.post('/api/validate-invite/', {
            'code': 'INVALID123'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is False
        assert 'error' in data
    
    def test_register_user_api_success(self, client):
        """Test successful user registration via API"""
        admin_user = User.objects.create_user(username='admin', password='testpass')
        invite = InviteCode.objects.create(
            code='REGAPI123',
            created_by=admin_user,
            task_group='general',
            role='member',
            max_uses=1
        )
        
        response = client.post('/api/register/', {
            'username': 'apiuser',
            'email': 'apiuser@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'API',
            'last_name': 'User',
            'invite_code': 'REGAPI123'
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['username'] == 'apiuser'
        assert data['role'] == 'member'
        assert data['task_group'] == 'general'
        
        # Check user was created
        user = User.objects.get(username='apiuser')
        assert user.email == 'apiuser@example.com'
        
        # Check profile was created
        profile = Profile.objects.get(user=user)
        assert profile.role == 'member'
        assert profile.task_group == 'general'
        
        # Check invite code was used
        invite.refresh_from_db()
        assert invite.used_count == 1
        assert user in invite.used_by.all()
    
    def test_register_user_api_invalid_invite(self, client):
        """Test user registration with invalid invite code via API"""
        response = client.post('/api/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'invite_code': 'INVALID123'
        })
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
    
    def test_register_user_api_duplicate_username(self, client):
        """Test user registration with duplicate username via API"""
        User.objects.create_user(username='existing', email='existing@example.com', password='testpass')
        admin_user = User.objects.create_user(username='admin', password='testpass')
        invite = InviteCode.objects.create(
            code='DUP123',
            created_by=admin_user,
            task_group='general',
            role='member'
        )
        
        response = client.post('/api/register/', {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'invite_code': 'DUP123'
        })
        
        assert response.status_code == 400
        data = response.json()
        assert 'username' in data


@pytest.mark.django_db
class TestInviteCodeAdmin:
    """Test invite code admin functionality"""
    
    def test_invite_code_admin_list_display(self, admin_client):
        """Test invite code admin list display"""
        admin_user, _ = User.objects.get_or_create(
            username='admin_invites', defaults={'email': 'admin_invites@example.com', 'is_superuser': True}
        )
        if not admin_user.check_password('testpass'):
            admin_user.set_password('testpass')
            admin_user.save()
        invite = InviteCode.objects.create(
            code='ADMIN123',
            created_by=admin_user,
            task_group='cleaning',
            role='member'
        )
        
        response = admin_client.get('/admin/api/invitecode/')
        assert response.status_code == 200
        assert 'ADMIN123' in response.content.decode()
        assert 'member' in response.content.decode()
        assert 'cleaning' in response.content.decode()
    
    def test_invite_code_admin_actions(self, admin_client):
        """Test invite code admin actions"""
        admin_user, _ = User.objects.get_or_create(
            username='admin_invites2', defaults={'email': 'admin_invites2@example.com', 'is_superuser': True}
        )
        if not admin_user.check_password('testpass'):
            admin_user.set_password('testpass')
            admin_user.save()
        invite1 = InviteCode.objects.create(
            code='ACTIVE123',
            created_by=admin_user,
            is_active=True
        )
        invite2 = InviteCode.objects.create(
            code='INACTIVE123',
            created_by=admin_user,
            is_active=False
        )
        
        # Test deactivate action
        response = admin_client.post('/admin/api/invitecode/', {
            'action': 'deactivate_codes',
            '_selected_action': [invite1.id]
        })
        assert response.status_code == 302
        
        invite1.refresh_from_db()
        assert invite1.is_active is False
        
        # Test activate action
        response = admin_client.post('/admin/api/invitecode/', {
            'action': 'activate_codes',
            '_selected_action': [invite1.id, invite2.id]
        })
        assert response.status_code == 302
        
        invite1.refresh_from_db()
        invite2.refresh_from_db()
        assert invite1.is_active is True
        assert invite2.is_active is True
