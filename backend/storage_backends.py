"""
Custom storage backends for Railway deployment
"""
import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class RailwayFileSystemStorage(FileSystemStorage):
    """
    Custom file system storage that handles Railway volume permissions
    """
    
    def _save(self, name, content):
        """
        Override _save to handle permission issues on Railway volumes
        """
        full_path = self.path(name)
        
        # Create directory with proper error handling
        directory = os.path.dirname(full_path)
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, mode=0o755, exist_ok=True)
        except PermissionError:
            # If we can't create the directory, try to save in the root
            print(f"⚠️ Cannot create directory {directory}, saving to root")
            name = os.path.basename(name)
            full_path = self.path(name)
        
        return super()._save(name, content)
    
    def get_available_name(self, name, max_length=None):
        """
        Override to ensure we have a valid filename
        """
        # If we can't create subdirectories, flatten the path
        if not self._can_create_directory(os.path.dirname(self.path(name))):
            name = os.path.basename(name)
        
        return super().get_available_name(name, max_length)
    
    def _can_create_directory(self, directory):
        """
        Check if we can create a directory
        """
        if os.path.exists(directory):
            return True
        
        try:
            os.makedirs(directory, mode=0o755, exist_ok=True)
            return True
        except PermissionError:
            return False