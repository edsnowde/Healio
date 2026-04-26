"""
Multimodal File Handler
Handles image and video uploads for clinical analysis
"""

import os
import logging
from typing import Optional, Dict
from pathlib import Path
import aiofiles
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultimodalFileHandler:
    """Handles file uploads and storage for multimodal clinical data"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Allowed file types
        self.allowed_images = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        self.allowed_videos = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        self.allowed_audio = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
        
        # Max file sizes (MB)
        self.max_image_size = 10
        self.max_video_size = 100
        self.max_audio_size = 50
    
    async def save_image(self, file_bytes: bytes, filename: str) -> Optional[Dict]:
        """
        Save clinical image for Gemini Vision analysis
        
        Args:
            file_bytes: Image file content
            filename: Original filename
        
        Returns:
            {
                "success": bool,
                "file_path": str,
                "file_id": str,
                "size_mb": float,
                "mimetype": str
            }
        """
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext not in self.allowed_images:
                return {
                    "success": False,
                    "error": f"Image type {file_ext} not allowed. Use: {self.allowed_images}"
                }
            
            file_size_mb = len(file_bytes) / (1024 * 1024)
            if file_size_mb > self.max_image_size:
                return {
                    "success": False,
                    "error": f"Image too large ({file_size_mb:.2f}MB). Max: {self.max_image_size}MB"
                }
            
            # Generate file ID
            file_id = self._generate_file_id(file_bytes)
            safe_filename = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            
            file_path = self.upload_dir / "images" / safe_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_bytes)
            
            logger.info(f"Image saved: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "file_id": file_id,
                "size_mb": round(file_size_mb, 2),
                "mimetype": f"image/{file_ext[1:]}",
                "type": "image"
            }
        
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_audio(self, file_bytes: bytes, filename: str) -> Optional[Dict]:
        """
        Save audio file for Speech-to-Text processing
        
        Args:
            file_bytes: Audio file content
            filename: Original filename
        
        Returns:
            {
                "success": bool,
                "file_path": str,
                "file_id": str,
                "size_mb": float,
                "mimetype": str
            }
        """
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext not in self.allowed_audio:
                return {
                    "success": False,
                    "error": f"Audio type {file_ext} not allowed. Use: {self.allowed_audio}"
                }
            
            file_size_mb = len(file_bytes) / (1024 * 1024)
            if file_size_mb > self.max_audio_size:
                return {
                    "success": False,
                    "error": f"Audio too large ({file_size_mb:.2f}MB). Max: {self.max_audio_size}MB"
                }
            
            # Generate file ID
            file_id = self._generate_file_id(file_bytes)
            safe_filename = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            
            file_path = self.upload_dir / "audio" / safe_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_bytes)
            
            logger.info(f"Audio saved: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "file_id": file_id,
                "size_mb": round(file_size_mb, 2),
                "mimetype": f"audio/{file_ext[1:]}",
                "type": "audio"
            }
        
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_video(self, file_bytes: bytes, filename: str) -> Optional[Dict]:
        """
        Save video file for Gemini Vision analysis
        
        Args:
            file_bytes: Video file content
            filename: Original filename
        
        Returns:
            {"success": bool, "file_path": str, ...}
        """
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext not in self.allowed_videos:
                return {
                    "success": False,
                    "error": f"Video type {file_ext} not allowed. Use: {self.allowed_videos}"
                }
            
            file_size_mb = len(file_bytes) / (1024 * 1024)
            if file_size_mb > self.max_video_size:
                return {
                    "success": False,
                    "error": f"Video too large ({file_size_mb:.2f}MB). Max: {self.max_video_size}MB"
                }
            
            file_id = self._generate_file_id(file_bytes)
            safe_filename = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            
            file_path = self.upload_dir / "videos" / safe_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_bytes)
            
            logger.info(f"Video saved: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "file_id": file_id,
                "size_mb": round(file_size_mb, 2),
                "mimetype": f"video/{file_ext[1:]}",
                "type": "video"
            }
        
        except Exception as e:
            logger.error(f"Error saving video: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _generate_file_id(file_bytes: bytes) -> str:
        """Generate unique file ID from content hash"""
        return hashlib.md5(file_bytes).hexdigest()[:12]
    
    def get_file_path(self, file_id: str, file_type: str = "image") -> Optional[str]:
        """Get path to previously saved file"""
        try:
            type_dir = self.upload_dir / file_type
            
            for file_path in type_dir.glob(f"{file_id}_*"):
                return str(file_path)
            
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving file: {str(e)}")
            return None


# Singleton instance
_file_handler = None

def get_file_handler() -> MultimodalFileHandler:
    """Get or create file handler singleton"""
    global _file_handler
    if _file_handler is None:
        _file_handler = MultimodalFileHandler()
    return _file_handler
