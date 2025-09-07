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


def _to_webp_safe_mode(img):
    """Convert image to WebP-safe mode - Agent's critical fix for CMYK/P crashes."""
    # Preserve alpha if present, else go RGB
    if img.mode in ("RGBA", "LA"):
        return img.convert("RGBA")
    # CMYK, P, I, L → RGB (prevents WebP crashes)
    if img.mode not in ("RGB", "RGBA"):
        return img.convert("RGB")
    return img


def _transpose_exif_orientation(img):
    """
    Apply EXIF orientation to image if present.
    Agent's enhancement: Proper orientation handling for mobile photos.
    """
    try:
        return ImageOps.exif_transpose(img)
    except Exception:
        # If no EXIF data or transpose fails, return original
        return img


def _resize_maintain_aspect(img, max_dimension):
    """
    Resize image maintaining aspect ratio.
    
    Args:
        img: PIL Image instance
        max_dimension: Maximum width or height
        
    Returns:
        PIL Image: Resized image
    """
    original_width, original_height = img.size
    
    if original_width <= max_dimension and original_height <= max_dimension:
        return img
    
    # Calculate new dimensions maintaining aspect ratio
    if original_width > original_height:
        new_width = max_dimension
        new_height = int((original_height * max_dimension) / original_width)
    else:
        new_height = max_dimension
        new_width = int((original_width * max_dimension) / original_height)
    
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def _optimize_quality(img, target_size, min_quality, use_webp):
    """
    Agent's iterative quality optimization to meet target file size.
    
    Args:
        img: PIL Image instance
        target_size: Target file size in bytes
        min_quality: Minimum quality threshold
        use_webp: Prefer WebP format
        
    Returns:
        bytes: Optimized image data
    """
    def encode_image(img_to_encode, quality, use_webp=True):
        """Encode image with specified quality and format."""
        output = BytesIO()
        
        if use_webp:
            # Agent's critical fix: Ensure WebP-safe mode to prevent crashes
            safe_img = _to_webp_safe_mode(img_to_encode)
            safe_img.save(output, format="WEBP", quality=quality, method=6)
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
    
    # Start with high quality and iteratively reduce
    qualities = [95, 85, 75, 65, 55, 45, 35] + list(range(min_quality, 25, -5))
    
    for quality in qualities:
        # Try WebP first if requested
        if use_webp:
            data = encode_image(img, quality, use_webp=True)
            if len(data) <= target_size:
                return data
        
        # Try JPEG fallback
        data = encode_image(img, quality, use_webp=False)
        if len(data) <= target_size:
            return data
    
    # If still too large, check if target is unreasonably small
    best_effort = encode_image(img, min_quality, use_webp=use_webp)
    if len(best_effort) > target_size * 2:  # If best effort is more than 2x target, fail
        raise ValueError(f"Cannot optimize image to target size {target_size} bytes. Best effort: {len(best_effort)} bytes")
    
    logger.warning(f"Could not optimize image to target size {target_size}, using minimum quality {min_quality}")
    return best_effort


def optimize_image(image_file, 
                  max_dimension: int = 2048, 
                  target_size: int = 5 * 1024 * 1024,
                  min_quality: int = 30,
                  use_webp: bool = True) -> tuple[bytes, dict]:
    """
    Agent's enhanced image optimization system.
    Accepts large files, optimizes to storage targets server-side.
    
    Args:
        image_file: Uploaded file object
        max_dimension: Maximum width/height (default 2048px)
        target_size: Target file size in bytes (default 5MB)
        min_quality: Minimum quality threshold (default 30)
        use_webp: Prefer WebP format (default True)
        
    Returns:
        tuple: (optimized_bytes, metadata_dict)
        
    Raises:
        ValueError: If image is invalid, corrupted, or exceeds safety limits
    """
    try:
        # Agent's critical fix: Decompression bomb protection
        # Prevent massive decompressed images that could consume excessive memory
        MAX_PIXELS = 178_956_970  # ~178MP (PIL default)
        MAX_DIMENSION_SINGLE = 16000  # Single dimension limit
        
        # Load and validate image with enhanced safety checks
        with Image.open(image_file) as img:
            # Check decompression bomb limits before processing
            width, height = img.size
            total_pixels = width * height
            
            # Agent's safety validation
            if total_pixels > MAX_PIXELS:
                raise ValueError(f"Image too large: {total_pixels:,} pixels exceeds {MAX_PIXELS:,} limit")
            
            if width > MAX_DIMENSION_SINGLE or height > MAX_DIMENSION_SINGLE:
                raise ValueError(f"Image dimensions too large: {width}x{height} exceeds {MAX_DIMENSION_SINGLE}px limit")
            
            # Capture original metadata
            original_size_bytes = len(image_file.read())
            image_file.seek(0)  # Reset for processing
            
            metadata = {
                'width': width,
                'height': height, 
                'original_size_bytes': original_size_bytes,
                'format': img.format,
                'mode': img.mode
            }
            
            # Agent's EXIF orientation handling
            img = _transpose_exif_orientation(img)
            
            # Resize if dimensions exceed limits
            current_img = img.copy() if hasattr(img, 'copy') else img
            if width > max_dimension or height > max_dimension:
                current_img = _resize_maintain_aspect(current_img, max_dimension)
                metadata['resized'] = True
                metadata['new_width'] = current_img.size[0]
                metadata['new_height'] = current_img.size[1]
            
            # Agent's iterative quality optimization
            optimized_bytes = _optimize_quality(current_img, target_size, min_quality, use_webp)
            metadata['size_bytes'] = len(optimized_bytes)
            metadata['compression_ratio'] = original_size_bytes / len(optimized_bytes) if len(optimized_bytes) > 0 else 1.0
            metadata['format_used'] = 'WebP' if use_webp else 'JPEG'
            
            return optimized_bytes, metadata
            
    except (OSError, IOError, ValueError) as e:
        # Handle PIL errors, corrupted images, and validation errors
        raise ValueError(f"Invalid or corrupted image: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors
        raise ValueError(f"Image processing failed: {str(e)}")


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
