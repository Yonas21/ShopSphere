from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os
import uuid
import shutil
from PIL import Image
from database.sql_database import get_db
from auth import get_current_active_user, get_admin_user
from models.user import User
from typing import List

router = APIRouter(prefix="/upload", tags=["upload"])

# Configuration
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_DIMENSION = 2048

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(exist_ok=True)

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {file.size} bytes exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )

def process_image(file_path: Path) -> None:
    """Process uploaded image (resize if too large, optimize)"""
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(file_path, optimize=True, quality=85)
    except Exception as e:
        # If image processing fails, remove the file
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user),  # Only admins can upload images
    db: Session = Depends(get_db)
):
    """Upload and process an image file"""
    try:
        # Validate the file
        validate_image_file(file)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process image (resize, optimize)
        process_image(file_path)
        
        # Return the file URL
        file_url = f"/api/upload/image/{unique_filename}"
        
        return {
            "message": "Image uploaded successfully",
            "filename": unique_filename,
            "url": file_url,
            "original_filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        await file.close()

@router.get("/image/{filename}")
async def get_image(filename: str):
    """Serve uploaded images"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        path=file_path,
        media_type="image/*",
        headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
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