from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os
import uuid
import shutil
import logging
from database.sql_database import get_db
from auth import get_current_active_user, get_admin_user
from models.user import User
from utils.image_processing import optimize_uploaded_image, image_processor, cdn_manager
from utils.validation import validate_file_upload
from utils.cache import cache_set, cache_get, cache_delete
from typing import List, Optional

logger = logging.getLogger("app.api.upload")
router = APIRouter(prefix="/upload", tags=["upload"])

# Configuration
UPLOAD_DIR = Path("uploads")
THUMBNAILS_DIR = UPLOAD_DIR / "thumbnails"
ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heif", ".heic"]

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
THUMBNAILS_DIR.mkdir(exist_ok=True)

async def validate_and_process_upload(file: UploadFile) -> bytes:
    """Validate and read uploaded file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Read file content
    try:
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer
    except Exception as e:
        logger.error(f"Failed to read uploaded file {file.filename}: {e}")
        raise HTTPException(status_code=400, detail="Failed to read file")
    
    # Validate using our enhanced validation
    try:
        validated_filename = validate_file_upload(
            file.filename,
            len(file_content),
            ALLOWED_EXTENSIONS,
            max_size_mb=10
        )
    except ValueError as e:
        logger.warning(f"File validation failed for {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    return file_content

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    create_thumbnail: bool = True,
    current_user: User = Depends(get_admin_user),  # Only admins can upload images
    db: Session = Depends(get_db)
):
    """Upload and process an image file with advanced optimization"""
    try:
        # Validate and read file
        file_content = await validate_and_process_upload(file)
        
        # Process image with advanced optimization
        processing_results = optimize_uploaded_image(
            file_content, 
            file.filename, 
            create_thumbnail=create_thumbnail
        )
        
        # Generate unique filenames
        unique_id = str(uuid.uuid4())
        optimized_filename = f"{unique_id}_{processing_results['optimized']['filename']}"
        
        # Save optimized image
        optimized_path = UPLOAD_DIR / optimized_filename
        with open(optimized_path, "wb") as f:
            f.write(processing_results['optimized']['content'])
        
        # Save thumbnail if created
        thumbnail_url = None
        thumbnail_filename = None
        if create_thumbnail and 'thumbnail' in processing_results:
            thumbnail_filename = f"{unique_id}_thumb.jpg"
            thumbnail_path = THUMBNAILS_DIR / thumbnail_filename
            with open(thumbnail_path, "wb") as f:
                f.write(processing_results['thumbnail']['content'])
            thumbnail_url = f"/api/upload/thumbnail/{thumbnail_filename}"
        
        # Generate URLs
        image_url = f"/api/upload/image/{optimized_filename}"
        
        # Try to upload to CDN if enabled
        cdn_url = cdn_manager.upload_to_cdn(processing_results['optimized']['content'], optimized_filename)
        
        # Cache image info for quick access
        cache_key = f"image_info:{optimized_filename}"
        image_info = {
            'filename': optimized_filename,
            'original_filename': file.filename,
            'url': cdn_url or image_url,
            'thumbnail_url': thumbnail_url,
            'size_bytes': processing_results['optimized']['size_bytes'],
            'original_size_bytes': processing_results['original_info']['size_bytes'],
            'compression_stats': processing_results['compression_stats']
        }
        cache_set(cache_key, image_info, ttl=3600)  # Cache for 1 hour
        
        logger.info(f"Image uploaded successfully: {file.filename} -> {optimized_filename}")
        logger.info(f"Size reduction: {processing_results['compression_stats']['savings_percent']:.1f}%")
        
        return {
            "message": "Image uploaded and optimized successfully",
            "filename": optimized_filename,
            "original_filename": file.filename,
            "url": cdn_url or image_url,
            "thumbnail_url": thumbnail_url,
            "size_bytes": processing_results['optimized']['size_bytes'],
            "original_size_bytes": processing_results['original_info']['size_bytes'],
            "compression_stats": processing_results['compression_stats'],
            "processing_info": {
                "format": processing_results['original_info']['format'],
                "dimensions": f"{processing_results['original_info']['width']}x{processing_results['original_info']['height']}",
                "optimized_format": Path(optimized_filename).suffix[1:].upper(),
                "has_thumbnail": create_thumbnail and 'thumbnail' in processing_results
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Image processing failed for {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected upload error for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        await file.close()

@router.get("/image/{filename}")
async def get_image(filename: str):
    """Serve uploaded images with caching"""
    # Check cache first
    cache_key = f"image_info:{filename}"
    cached_info = cache_get(cache_key)
    
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        # Clean up cache if file doesn't exist
        if cached_info:
            cache_delete(cache_key)
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        path=file_path,
        media_type="image/*",
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            "ETag": f'"{filename}"',
            "X-Content-Type-Options": "nosniff"
        }
    )

@router.get("/thumbnail/{filename}")
async def get_thumbnail(filename: str):
    """Serve thumbnail images"""
    file_path = THUMBNAILS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            "ETag": f'"{filename}"',
            "X-Content-Type-Options": "nosniff"
        }
    )

@router.delete("/image/{filename}")
async def delete_image(
    filename: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete an uploaded image"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        file_path.unlink()
        return {"message": "Image deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

@router.get("/images")
async def list_images(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all uploaded images (admin only)"""
    try:
        images = []
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                stat = file_path.stat()
                images.append({
                    "filename": file_path.name,
                    "url": f"/api/upload/image/{file_path.name}",
                    "size": stat.st_size,
                    "created_at": stat.st_ctime
                })
        
        # Sort by creation time (newest first)
        images.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list images: {str(e)}")