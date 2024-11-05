# file_manager.py

import os
import shutil
import time
from datetime import datetime, timedelta
import logging
from threading import Lock
import uuid

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_temp_dir='tmp', max_age_hours=24):
        self.base_temp_dir = base_temp_dir
        self.max_age = timedelta(hours=max_age_hours)
        self.lock = Lock()
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for dir_path in [self.base_temp_dir, 
                        os.path.join('static', 'visualizations')]:
            os.makedirs(dir_path, exist_ok=True)

    def generate_temp_path(self, original_filename):
        """Generate a unique temporary file path"""
        ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        return os.path.join(self.base_temp_dir, unique_filename)

    def save_uploaded_file(self, file_obj):
        """Save an uploaded file and return its path"""
        temp_path = self.generate_temp_path(file_obj.filename)
        file_obj.save(temp_path)
        return temp_path

    def cleanup_old_files(self):
        """Remove files older than max_age"""
        with self.lock:
            current_time = datetime.now()
            try:
                # Cleanup temporary files
                for filename in os.listdir(self.base_temp_dir):
                    file_path = os.path.join(self.base_temp_dir, filename)
                    if self._is_old_file(file_path, current_time):
                        self._safe_remove(file_path)

                # Cleanup visualizations
                vis_dir = os.path.join('static', 'visualizations')
                for filename in os.listdir(vis_dir):
                    file_path = os.path.join(vis_dir, filename)
                    if self._is_old_file(file_path, current_time):
                        self._safe_remove(file_path)

            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")

    def _is_old_file(self, file_path, current_time):
        """Check if file is older than max_age"""
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            return (current_time - mtime) > self.max_age
        except Exception as e:
            logger.error(f"Error checking file age for {file_path}: {str(e)}")
            return False

    def _safe_remove(self, file_path):
        """Safely remove a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed old file: {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")

    def cleanup_file(self, file_path):
        """Remove a specific file"""
        with self.lock:
            self._safe_remove(file_path)