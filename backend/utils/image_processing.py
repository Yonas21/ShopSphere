"""
Image processing utilities for optimization and compression
"""
import os
import io
from typing import Tuple, Optional, BinaryIO, Union
from pathlib import Path
import logging
from PIL import Image, ImageOps, ImageFilter
# Handle different Pillow versions for EXIF orientation
try:
    from PIL.ExifTags import Base as ExifBase
    ORIENTATION = ExifBase.Orientation.value
except (ImportError, AttributeError):
    try:
        from PIL.ExifTags import ORIENTATION
    except ImportError:
        ORIENTATION = 274  # Standard EXIF orientation tag
import pillow_heif
from pydantic_settings import BaseSettings

logger = logging.getLogger("app.image_processing")

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

class ImageSettings(BaseSettings):
    # Image size limits
    max_image_width: int = 1920
    max_image_height: int = 1080
    thumbnail_width: int = 300
    thumbnail_height: int = 300
    
    # Quality settings
    jpeg_quality: int = 85
    webp_quality: int = 80
    png_compress_level: int = 6
    
    # File size limits (in bytes)
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    target_file_size: int = 1 * 1024 * 1024  # 1MB target after compression
    
    # Supported formats
    supported_input_formats: list = ["JPEG", "JPG", "PNG", "GIF", "WEBP", "HEIF", "HEIC", "BMP"]
    output_format: str = "WEBP"  # Default output format for best compression
    fallback_format: str = "JPEG"  # Fallback if WebP not supported
    
    # CDN settings (placeholder for future CDN integration)
    cdn_enabled: bool = False
    cdn_base_url: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = ImageSettings()

class ImageProcessor:
    """
    Advanced image processing with compression, resizing, and optimization
    """
    
    def __init__(self):
        self.supported_formats = set(settings.supported_input_formats)
    
    def validate_image(self, file_content: bytes, filename: str) -> bool:
        """
        Validate image file before processing
        
        Args:
            file_content: Image file bytes
            filename: Original filename
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check file size
            if len(file_content) > settings.max_file_size:
                logger.warning(f"Image {filename} exceeds size limit ({len(file_content)} bytes)")
                return False
            
            # Try to open image
            with Image.open(io.BytesIO(file_content)) as img:
                # Check if format is supported
                if img.format not in self.supported_formats:
                    logger.warning(f"Unsupported format {img.format} for {filename}")
                    return False
                
                # Check image dimensions (reasonable limits)
                if img.width > 10000 or img.height > 10000:
                    logger.warning(f"Image {filename} dimensions too large ({img.width}x{img.height})")
                    return False
                
                # Verify image is not corrupted
                img.verify()
                
            return True
            
        except Exception as e:
            logger.error(f"Image validation failed for {filename}: {e}")
            return False
    
    def fix_image_orientation(self, image: Image.Image) -> Image.Image:
        """
        Fix image orientation based on EXIF data
        
        Args:
            image: PIL Image object
            
        Returns:
            Image: Oriented image
        """
        try:
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    orientation = exif.get(ORIENTATION, 1)
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
        except Exception as e:
            logger.debug(f"Could not fix orientation: {e}")
        
        return image
    
    def optimize_image(
        self,
        file_content: bytes,
        filename: str,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: Optional[int] = None,
        output_format: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        Optimize image with compression and resizing
        
        Args:
            file_content: Original image bytes
            filename: Original filename
            max_width: Maximum width (defaults to settings)
            max_height: Maximum height (defaults to settings)
            quality: Compression quality (defaults to settings)
            output_format: Output format (defaults to settings)
            
        Returns:
            Tuple[bytes, str]: Optimized image bytes and new filename
        """
        if not self.validate_image(file_content, filename):
            raise ValueError(f"Invalid image: {filename}")
        
        # Set defaults
        max_width = max_width or settings.max_image_width
        max_height = max_height or settings.max_image_height
        output_format = output_format or settings.output_format
        
        try:
            with Image.open(io.BytesIO(file_content)) as image:
                # Convert to RGB if necessary (for JPEG/WebP)
                if image.mode in ('RGBA', 'LA', 'P'):
                    if output_format.upper() in ('JPEG', 'JPG'):
                        # Create white background for JPEG
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        if image.mode == 'P':
                            image = image.convert('RGBA')
                        background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                        image = background
                    elif output_format.upper() == 'WEBP':
                        image = image.convert('RGBA')
                    else:
                        image = image.convert('RGB')
                elif image.mode == 'L':  # Grayscale
                    if output_format.upper() not in ('PNG', 'WEBP'):
                        image = image.convert('RGB')
                
                # Fix orientation
                image = self.fix_image_orientation(image)
                
                # Calculate new dimensions
                original_width, original_height = image.size
                if original_width <= max_width and original_height <= max_height:
                    # No resizing needed
                    new_width, new_height = original_width, original_height
                else:
                    # Calculate aspect ratio preserving dimensions
                    ratio = min(max_width / original_width, max_height / original_height)
                    new_width = int(original_width * ratio)
                    new_height = int(original_height * ratio)
                
                # Resize if needed
                if (new_width, new_height) != (original_width, original_height):
                    # Use high-quality resampling
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.debug(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
                
                # Apply slight sharpening after resize
                if (new_width, new_height) != (original_width, original_height):
                    image = image.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=3))
                
                # Optimize and save
                output_buffer = io.BytesIO()
                
                # Set quality based on format
                save_kwargs = {}
                if output_format.upper() in ('JPEG', 'JPG'):
                    save_kwargs = {
                        'format': 'JPEG',
                        'quality': quality or settings.jpeg_quality,
                        'optimize': True,
                        'progressive': True
                    }
                    new_filename = Path(filename).stem + '.jpg'
                elif output_format.upper() == 'WEBP':
                    save_kwargs = {
                        'format': 'WEBP',
                        'quality': quality or settings.webp_quality,
                        'optimize': True,
                        'method': 6  # Best compression
                    }
                    new_filename = Path(filename).stem + '.webp'
                elif output_format.upper() == 'PNG':
                    save_kwargs = {
                        'format': 'PNG',
                        'optimize': True,
                        'compress_level': settings.png_compress_level
                    }
                    new_filename = Path(filename).stem + '.png'
                else:
                    # Fallback to JPEG
                    save_kwargs = {
                        'format': 'JPEG',
                        'quality': quality or settings.jpeg_quality,
                        'optimize': True
                    }
                    new_filename = Path(filename).stem + '.jpg'
                
                image.save(output_buffer, **save_kwargs)
                optimized_content = output_buffer.getvalue()
                
                # Log optimization results
                original_size = len(file_content)
                optimized_size = len(optimized_content)
                compression_ratio = (1 - optimized_size / original_size) * 100
                
                logger.info(f"Image optimized: {filename} -> {new_filename}")
                logger.info(f"Size: {original_size} -> {optimized_size} bytes ({compression_ratio:.1f}% reduction)")
                logger.info(f"Dimensions: {original_width}x{original_height} -> {new_width}x{new_height}")
                
                return optimized_content, new_filename
                
        except Exception as e:
            logger.error(f"Image optimization failed for {filename}: {e}")
            raise ValueError(f"Failed to optimize image: {str(e)}")
    
    def create_thumbnail(
        self,
        file_content: bytes,
        filename: str,
        size: Tuple[int, int] = None
    ) -> Tuple[bytes, str]:
        """
        Create thumbnail from image
        
        Args:
            file_content: Original image bytes
            filename: Original filename
            size: Thumbnail size (width, height)
            
        Returns:
            Tuple[bytes, str]: Thumbnail bytes and filename
        """
        if not self.validate_image(file_content, filename):
            raise ValueError(f"Invalid image: {filename}")
        
        size = size or (settings.thumbnail_width, settings.thumbnail_height)
        
        try:
            with Image.open(io.BytesIO(file_content)) as image:
                # Fix orientation
                image = self.fix_image_orientation(image)
                
                # Create thumbnail with aspect ratio preservation
                image.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Convert to RGB for JPEG
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                    image = background
                
                # Save thumbnail
                output_buffer = io.BytesIO()
                image.save(
                    output_buffer,
                    format='JPEG',
                    quality=settings.jpeg_quality,
                    optimize=True
                )
                
                thumbnail_content = output_buffer.getvalue()
                thumbnail_filename = f"thumb_{Path(filename).stem}.jpg"
                
                logger.info(f"Thumbnail created: {thumbnail_filename} ({len(thumbnail_content)} bytes)")
                
                return thumbnail_content, thumbnail_filename
                
        except Exception as e:
            logger.error(f"Thumbnail creation failed for {filename}: {e}")
            raise ValueError(f"Failed to create thumbnail: {str(e)}")
    
    def get_image_info(self, file_content: bytes, filename: str) -> dict:
        """
        Get image metadata and information
        
        Args:
            file_content: Image bytes
            filename: Original filename
            
        Returns:
            dict: Image information
        """
        if not self.validate_image(file_content, filename):
            raise ValueError(f"Invalid image: {filename}")
        
        try:
            with Image.open(io.BytesIO(file_content)) as image:
                info = {
                    'filename': filename,
                    'format': image.format,
                    'mode': image.mode,
                    'width': image.width,
                    'height': image.height,
                    'size_bytes': len(file_content),
                    'size_human': self._format_file_size(len(file_content)),
                    'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info,
                    'animated': getattr(image, 'is_animated', False),
                }
                
                # Add EXIF data if available
                if hasattr(image, '_getexif') and image._getexif():
                    exif = image._getexif()
                    info['has_exif'] = True
                    if ORIENTATION in exif:
                        info['orientation'] = exif[ORIENTATION]
                else:
                    info['has_exif'] = False
                
                return info
                
        except Exception as e:
            logger.error(f"Failed to get image info for {filename}: {e}")
            raise ValueError(f"Failed to analyze image: {str(e)}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

class CDNManager:
    """
    CDN integration manager (placeholder for future implementation)
    """
    
    def __init__(self):
        self.enabled = settings.cdn_enabled
        self.base_url = settings.cdn_base_url
    
    def upload_to_cdn(self, file_content: bytes, filename: str) -> Optional[str]:
        """
        Upload file to CDN
        
        Args:
            file_content: File bytes
            filename: Filename
            
        Returns:
            Optional[str]: CDN URL if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        # Placeholder for CDN implementation
        # This could integrate with AWS S3, Cloudflare, etc.
        logger.info(f"CDN upload placeholder for {filename}")
        return None
    
    def get_cdn_url(self, filename: str) -> Optional[str]:
        """
        Get CDN URL for a file
        
        Args:
            filename: Filename
            
        Returns:
            Optional[str]: CDN URL if available, None otherwise
        """
        if not self.enabled or not self.base_url:
            return None
        
        return f"{self.base_url.rstrip('/')}/{filename}"

# Global instances
image_processor = ImageProcessor()
cdn_manager = CDNManager()

# Convenience functions
def optimize_uploaded_image(
    file_content: bytes,
    filename: str,
    create_thumbnail: bool = True
) -> dict:
    """
    Complete image processing workflow
    
    Args:
        file_content: Original image bytes
        filename: Original filename
        create_thumbnail: Whether to create thumbnail
        
    Returns:
        dict: Processing results with optimized image and thumbnail
    """
    results = {}
    
    try:
        # Get original image info
        results['original_info'] = image_processor.get_image_info(file_content, filename)
        
        # Optimize main image
        optimized_content, optimized_filename = image_processor.optimize_image(file_content, filename)
        results['optimized'] = {
            'content': optimized_content,
            'filename': optimized_filename,
            'size_bytes': len(optimized_content)
        }
        
        # Create thumbnail if requested
        if create_thumbnail:
            thumbnail_content, thumbnail_filename = image_processor.create_thumbnail(file_content, filename)
            results['thumbnail'] = {
                'content': thumbnail_content,
                'filename': thumbnail_filename,
                'size_bytes': len(thumbnail_content)
            }
        
        # Calculate total savings
        original_size = len(file_content)
        optimized_size = len(optimized_content)
        savings = original_size - optimized_size
        savings_percent = (savings / original_size) * 100 if original_size > 0 else 0
        
        results['compression_stats'] = {
            'original_size': original_size,
            'optimized_size': optimized_size,
            'savings_bytes': savings,
            'savings_percent': savings_percent
        }
        
        logger.info(f"Image processing complete: {filename} -> {optimized_filename}")
        logger.info(f"Total savings: {savings} bytes ({savings_percent:.1f}%)")
        
        return results
        
    except Exception as e:
        logger.error(f"Image processing failed for {filename}: {e}")
        raise