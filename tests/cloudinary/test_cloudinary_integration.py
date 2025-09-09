#!/usr/bin/env python
"""
Cloudinary Integration Test
==========================

Test script to verify Cloudinary configuration is working properly with our 
existing enhanced image optimization system.

Run with: python test_cloudinary_integration.py
"""

import os
import sys
import django
from io import BytesIO

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from api.models import Property, Task, TaskImage
from django.conf import settings

def main():
    print("🔧 Cloudinary Integration Test")
    print("=" * 50)
    
    # Check if Cloudinary is enabled
    print(f"USE_CLOUDINARY: {getattr(settings, 'USE_CLOUDINARY', False)}")
    print(f"Storage backend: {settings.STORAGES['default']['BACKEND']}")
    
    if hasattr(settings, 'CLOUDINARY_STORAGE'):
        print(f"Cloudinary config: {settings.CLOUDINARY_STORAGE}")
    
    print()
    
    try:
        # Clean up any existing test data
        User.objects.filter(username="cloudtest").delete()
        Property.objects.filter(name="Cloud Test").delete()
        
        print("1. Creating test user, property, and task...")
        u = User.objects.create_user("cloudtest", "t@example.com", "testpass123")
        p = Property.objects.create(name="Cloud Test", address="123 Cloud Street")
        t = Task.objects.create(title="Cloudinary Check", property_ref=p, created_by=u)
        print(f"   ✅ Created Task ID: {t.pk}")
        
        print("2. Testing small GIF upload...")
        # Tiny red dot GIF (43 bytes)
        img_bytes = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\x00\x00\x00\x00\x00!\xf9\x04\x01\n\x00\x01\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        cf = ContentFile(img_bytes, name="cloudinary_test_dot.gif")
        
        # Create TaskImage directly (bypasses our optimization - just for testing storage)
        ti = TaskImage.objects.create(
            task=t, 
            uploaded_by=u, 
            image=cf, 
            size_bytes=len(img_bytes),
            width=1, 
            height=1, 
            original_size_bytes=len(img_bytes)
        )
        
        print(f"   ✅ TaskImage created with ID: {ti.pk}")
        print(f"   📁 File URL: {ti.image.url}")
        
        # Check if it's a Cloudinary URL
        if 'cloudinary.com' in ti.image.url or 'res.cloudinary.com' in ti.image.url:
            print("   🎉 SUCCESS: File uploaded to Cloudinary!")
            print(f"   🌐 Cloudinary URL detected: {ti.image.url}")
        elif ti.image.url.startswith('/media/'):
            print("   ⚠️  Local storage URL detected (Cloudinary might be disabled)")
            print(f"   💾 Local URL: {ti.image.url}")
        else:
            print(f"   ❓ Unknown URL format: {ti.image.url}")
        
        print()
        print("3. Testing with our enhanced optimization system...")
        
        # Test with our actual optimization pipeline (simulating API upload)
        from api.serializers import TaskImageSerializer
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create a larger test image to trigger optimization
        from PIL import Image
        test_img = Image.new('RGB', (800, 600), color='blue')
        img_buffer = BytesIO()
        test_img.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            name="cloudinary_optimization_test.jpg",
            content=img_buffer.getvalue(),
            content_type="image/jpeg"
        )
        
        # Test through serializer (this will trigger our optimization)
        data = {
            'image': uploaded_file,
            'task': t.pk
        }
        
        serializer = TaskImageSerializer(data=data)
        if serializer.is_valid():
            optimized_image = serializer.save(uploaded_by=u)
            
            print(f"   ✅ Optimized TaskImage created with ID: {optimized_image.pk}")
            print(f"   📊 Original size: {optimized_image.original_size_bytes} bytes")
            print(f"   📊 Optimized size: {optimized_image.size_bytes} bytes")
            
            if optimized_image.original_size_bytes and optimized_image.size_bytes:
                compression_ratio = optimized_image.original_size_bytes / optimized_image.size_bytes
                print(f"   📈 Compression ratio: {compression_ratio:.2f}x")
            
            print(f"   🌐 Optimized image URL: {optimized_image.image.url}")
            
            # Check if optimization + Cloudinary worked together
            if 'cloudinary.com' in optimized_image.image.url or 'res.cloudinary.com' in optimized_image.image.url:
                print("   🚀 PERFECT: Enhanced optimization + Cloudinary working together!")
            else:
                print("   📁 File stored locally (check USE_CLOUDINARY setting)")
                
        else:
            print(f"   ❌ Serializer validation failed: {serializer.errors}")
        
        print()
        print("4. Configuration Summary:")
        print(f"   • Storage Backend: {settings.STORAGES['default']['BACKEND']}")
        print(f"   • Media URL: {settings.MEDIA_URL}")
        print(f"   • USE_CLOUDINARY: {getattr(settings, 'USE_CLOUDINARY', False)}")
        
        # Check environment variable
        cloudinary_url = os.getenv('CLOUDINARY_URL')
        if cloudinary_url:
            print(f"   • CLOUDINARY_URL: {cloudinary_url[:30]}..." if len(cloudinary_url) > 30 else f"   • CLOUDINARY_URL: {cloudinary_url}")
        else:
            print("   • CLOUDINARY_URL: Not set")
        
        print()
        print("🎉 Cloudinary integration test completed!")
        
        if 'cloudinary.com' in ti.image.url:
            print("✅ Cloudinary is working correctly with your enhanced image system!")
        elif not getattr(settings, 'USE_CLOUDINARY', False):
            print("ℹ️  Cloudinary is disabled (USE_CLOUDINARY=False). Set to True to enable.")
        else:
            print("⚠️  Cloudinary might not be configured properly. Check your CLOUDINARY_URL.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test data
        try:
            print("\n🧹 Cleaning up test data...")
            User.objects.filter(username="cloudtest").delete()
            Property.objects.filter(name="Cloud Test").delete()
            print("✅ Cleanup completed")
        except:
            pass

if __name__ == '__main__':
    main()
