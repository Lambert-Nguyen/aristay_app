"""
Image optimization utilities for task evidence uploads.

Agent's enhanced approach: Accept large images (up to 25MB) from users,
then server-side optimize to storage target (≤5MB) with quality compression
and dimension scaling while preserving good visual quality.
"""

from io import BytesIO
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError
import logging

logger = logging.getLogger(__name__)

# Optional: Support HEIC/HEIF formats (iPhone photos)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    logger.info("HEIC/HEIF support enabled")
except ImportError:
    logger.info("HEIC/HEIF support not available (install pillow-heif)")
except Exception as e:
    logger.warning(f"HEIC/HEIF support failed to initialize: {e}")

# Supported input formats
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "HEIC", "HEIF"}


def validate_max_upload(file):
    """
    Validate file doesn't exceed ingress limit before processing.
    
    Args:
        file: Django UploadedFile instance
        
    Raises:
        ValidationError: If file exceeds MAX_UPLOAD_BYTES
    """
    max_bytes = getattr(settings, 'MAX_UPLOAD_BYTES', 25 * 1024 * 1024)
    
    if file.size > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise ValidationError(f"Image is too large (> {max_mb} MB). Please choose a smaller photo.")


def optimize_image(file, target_bytes=None, max_dim=None, min_quality=45):
    """
    Optimize uploaded image for storage - Agent's comprehensive approach.
    
    Process:
    1. Fix EXIF orientation issues
    2. Downscale to max dimension if needed
    3. Compress with quality reduction until under target size
    4. Final dimension reduction if still too large
    
    Args:
        file: Django UploadedFile instance
        target_bytes: Target file size (default: STORED_IMAGE_TARGET_BYTES)
        max_dim: Maximum dimension in pixels (default: STORED_IMAGE_MAX_DIM)
        min_quality: Minimum quality before giving up (default: 45)
        
    Returns:
        ContentFile: Optimized image file ready for storage
        None: If image cannot be optimized to target size
        
    Raises:
        ValidationError: If image is corrupt or unsupported format
    """
    target_bytes = target_bytes or getattr(settings, 'STORED_IMAGE_TARGET_BYTES', 5 * 1024 * 1024)
    max_dim = max_dim or getattr(settings, 'STORED_IMAGE_MAX_DIM', 2048)
    
    logger.info(f"Optimizing image: {file.name} ({file.size} bytes) -> target: {target_bytes} bytes")
    
    # Read file once and parse
    file.seek(0)  # Ensure we're at start
    raw_data = file.read()
    
    try:
        img = Image.open(BytesIO(raw_data))
        # Fix EXIF orientation issues (critical for mobile photos)
        img = ImageOps.exif_transpose(img)
    except UnidentifiedImageError:
        raise ValidationError("Invalid or corrupted image file.")
    
    # Validate format
    original_format = (img.format or "JPEG").upper()
    if original_format not in ALLOWED_FORMATS:
        supported = ", ".join(sorted(ALLOWED_FORMATS))
        raise ValidationError(f"Unsupported image format. Supported: {supported}")
    
    logger.info(f"Image details: {img.size} ({original_format})")
    
    # Step 1: Downscale dimensions if needed
    original_size = img.size
    w, h = img.size
    long_edge = max(w, h)
    
    if long_edge > max_dim:
        scale_factor = max_dim / float(long_edge)
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor) 
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        logger.info(f"Downscaled: {original_size} -> {img.size}")
    
    # Step 2: Optimize format and quality
    def encode_image(img_to_encode, quality, use_webp=True):
        """Encode image with specified quality and format."""
        output = BytesIO()
        
        if use_webp and img_to_encode.mode in ('RGBA', 'LA'):
            # WebP with transparency
            img_to_encode.save(output, format="WEBP", quality=quality, method=6, lossless=False)
        elif use_webp:
            # WebP without transparency  
            img_to_encode.save(output, format="WEBP", quality=quality, method=6)
        else:
            # JPEG fallback (convert RGBA to RGB)
            if img_to_encode.mode in ('RGBA', 'LA', 'P'):
                # Convert to RGB for JPEG
                rgb_img = Image.new('RGB', img_to_encode.size, (255, 255, 255))
                if img_to_encode.mode == 'P':
                    img_to_encode = img_to_encode.convert('RGBA')
                rgb_img.paste(img_to_encode, mask=img_to_encode.split()[-1] if img_to_encode.mode in ('RGBA', 'LA') else None)
                rgb_img.save(output, format="JPEG", quality=quality, optimize=True, progressive=True)
            else:
                img_to_encode.save(output, format="JPEG", quality=quality, optimize=True, progressive=True)
        
        return output.getvalue()
    
    # Step 3: Iterative quality reduction (prefer WebP)
    quality = 85
    try_webp = True
    encoded_data = encode_image(img, quality, try_webp)
    
    # Reduce quality until under target or minimum reached
    while len(encoded_data) > target_bytes and quality > min_quality:
        quality = max(min_quality, quality - 10)
        encoded_data = encode_image(img, quality, try_webp)
        logger.info(f"Quality {quality}: {len(encoded_data)} bytes")
    
    # Step 4: If still too large, try further dimension reduction
    dimension_passes = 0
    max_dimension_passes = 3
    
    while (len(encoded_data) > target_bytes and 
           max(img.size) > 1024 and 
           dimension_passes < max_dimension_passes):
        
        # Reduce dimensions by 20%
        w, h = img.size
        new_w, new_h = int(w * 0.8), int(h * 0.8)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Reduce quality slightly
        quality = max(min_quality, quality - 5)
        encoded_data = encode_image(img, quality, try_webp)
        dimension_passes += 1
        
        logger.info(f"Dimension pass {dimension_passes}: {img.size}, quality {quality}, {len(encoded_data)} bytes")
    
    # Step 5: Check if optimization succeeded
    if len(encoded_data) > target_bytes:
        target_mb = target_bytes / (1024 * 1024)
        actual_mb = len(encoded_data) / (1024 * 1024)
        logger.warning(f"Could not optimize to target: {actual_mb:.1f}MB > {target_mb:.1f}MB")
        return None
    
    # Success! Create optimized file
    file_extension = ".webp" if try_webp else ".jpg"
    original_name = getattr(file, 'name', 'upload')
    base_name = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
    optimized_name = f"{base_name}_optimized{file_extension}"
    
    final_size_mb = len(encoded_data) / (1024 * 1024)
    logger.info(f"Optimization successful: {file.size} -> {len(encoded_data)} bytes ({final_size_mb:.2f}MB)")
    
    return ContentFile(encoded_data, name=optimized_name)


def get_image_metadata(file):
    """
    Extract metadata from optimized image for database storage.
    
    Args:
        file: ContentFile with optimized image data
        
    Returns:
        dict: Metadata including width, height, size_bytes, format
    """
    file.seek(0)
    try:
        img = Image.open(file)
        return {
            'width': img.width,
            'height': img.height,
            'size_bytes': file.size,
            'format': img.format or 'UNKNOWN'
        }
    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}")
        return {
            'width': None,
            'height': None,
            'size_bytes': file.size,
            'format': 'UNKNOWN'
        }
    finally:
        file.seek(0)
