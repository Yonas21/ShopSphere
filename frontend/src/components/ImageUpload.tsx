import React, { useState, useRef } from 'react';
import axios from 'axios';

interface ImageUploadProps {
  onImageUploaded: (imageUrl: string) => void;
  currentImageUrl?: string;
  token: string;
  disabled?: boolean;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ 
  onImageUploaded, 
  currentImageUrl, 
  token, 
  disabled = false 
}) => {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(currentImageUrl || null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_BASE_URL = 'http://localhost:8000';

  const validateFile = (file: File): string | null => {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return 'Please select a valid image file (JPEG, PNG, GIF, or WebP)';
    }

    if (file.size > maxSize) {
      return 'File size must be less than 10MB';
    }

    return null;
  };

  const handleFileSelect = (file: File) => {
    const error = validateFile(file);
    if (error) {
      alert(`❌ ${error}`);
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Upload file
    uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${API_BASE_URL}/api/upload/image`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total 
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setUploadProgress(progress);
          },
        }
      );

      const fullImageUrl = `${API_BASE_URL}${response.data.url}`;
      onImageUploaded(fullImageUrl);
      
      // Success notification
      const notification = document.createElement('div');
      notification.innerHTML = `
        <div style="
          position: fixed;
          top: 20px;
          right: 20px;
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          padding: 1rem 1.5rem;
          border-radius: 12px;
          box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
          z-index: 10000;
          font-weight: 500;
          animation: slideIn 0.3s ease-out;
        ">
          ✅ Image uploaded successfully!
        </div>
        <style>
          @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
        </style>
      `;
      document.body.appendChild(notification);
      setTimeout(() => notification.remove(), 3000);

    } catch (error: any) {
      console.error('Upload error:', error);
      alert(`❌ Upload failed: ${error.response?.data?.detail || 'Please try again'}`);
      setPreview(currentImageUrl || null);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    if (disabled || uploading) return;

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const removeImage = () => {
    setPreview(null);
    onImageUploaded('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div style={{ width: '100%' }}>
      <label style={{ 
        display: 'block', 
        marginBottom: '0.5rem', 
        fontWeight: '600', 
        color: '#374151',
        fontSize: '0.95rem'
      }}>
        📷 Product Image
      </label>

      {preview ? (
        <div style={{
          position: 'relative',
          borderRadius: '12px',
          overflow: 'hidden',
          border: '2px solid #e5e7eb',
          backgroundColor: '#f8fafc'
        }}>
          <img
            src={preview}
            alt="Preview"
            style={{
              width: '100%',
              height: '200px',
              objectFit: 'cover',
              display: 'block'
            }}
          />
          
          {uploading && (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.7)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white'
            }}>
              <div style={{ marginBottom: '1rem', fontSize: '1.1rem', fontWeight: '600' }}>
                Uploading... {uploadProgress}%
              </div>
              <div style={{
                width: '60%',
                height: '8px',
                backgroundColor: 'rgba(255, 255, 255, 0.3)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${uploadProgress}%`,
                  height: '100%',
                  backgroundColor: '#10b981',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
          )}

          {!uploading && (
            <div style={{
              position: 'absolute',
              top: '0.5rem',
              right: '0.5rem',
              display: 'flex',
              gap: '0.5rem'
            }}>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                style={{
                  padding: '0.5rem',
                  backgroundColor: 'rgba(0, 0, 0, 0.7)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '500'
                }}
                title="Change image"
              >
                ✏️
              </button>
              <button
                onClick={removeImage}
                disabled={disabled}
                style={{
                  padding: '0.5rem',
                  backgroundColor: 'rgba(220, 38, 38, 0.9)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '500'
                }}
                title="Remove image"
              >
                🗑️
              </button>
            </div>
          )}
        </div>
      ) : (
        <div
          style={{
            border: dragOver ? '2px dashed #667eea' : '2px dashed #d1d5db',
            borderRadius: '12px',
            padding: '2rem',
            textAlign: 'center',
            backgroundColor: dragOver ? '#f0f9ff' : disabled ? '#f9fafb' : '#fafafa',
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            minHeight: '200px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          onClick={() => !disabled && !uploading && fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {uploading ? (
            <div style={{ color: '#667eea' }}>
              <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
              <div style={{ marginBottom: '1rem', fontSize: '1.1rem', fontWeight: '600' }}>
                Uploading... {uploadProgress}%
              </div>
              <div style={{
                width: '200px',
                height: '8px',
                backgroundColor: '#e5e7eb',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${uploadProgress}%`,
                  height: '100%',
                  backgroundColor: '#667eea',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
          ) : (
            <div style={{ color: disabled ? '#9ca3af' : '#64748b' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📷</div>
              <div style={{ marginBottom: '0.5rem', fontSize: '1.1rem', fontWeight: '600' }}>
                {disabled ? 'Image upload disabled' : 'Drop image here or click to upload'}
              </div>
              <div style={{ fontSize: '0.9rem' }}>
                {disabled ? '' : 'Supports JPEG, PNG, GIF, WebP (max 10MB)'}
              </div>
            </div>
          )}
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileInputChange}
        disabled={disabled || uploading}
        style={{ display: 'none' }}
      />

      <div style={{ 
        marginTop: '0.5rem', 
        fontSize: '0.8rem', 
        color: '#64748b',
        textAlign: 'center'
      }}>
        💡 Images are automatically resized and optimized for better performance
      </div>
    </div>
  );
};

export default ImageUpload;