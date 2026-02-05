"""
Custom storage backends for Railway deployment
"""

import os
import tempfile

from django.core.files.storage import FileSystemStorage


class RailwayFileSystemStorage(FileSystemStorage):
    """
    Custom file system storage that handles Railway volume permissions
    """

    def _save(self, name, content):
        """
        Override _save to handle permission issues on Railway volumes
        """
        # Try the normal save first
        try:
            return super()._save(name, content)
        except PermissionError as e:
            print(f"⚠️ Permission denied saving {name}: {e}")

            # Fallback: use /tmp directory which is always writable
            fallback_root = "/tmp/media"
            os.makedirs(fallback_root, exist_ok=True)

            # Create a new storage instance pointing to /tmp
            fallback_storage = FileSystemStorage(location=fallback_root)

            # Save to fallback location
            saved_name = fallback_storage._save(name, content)
            print(f"📁 Saved to fallback location: {fallback_root}/{saved_name}")

            # Update our location to the fallback for future operations
            self.location = fallback_root

            return saved_name

    def url(self, name):
        """
        Generate URL for the file
        """
        if not name:
            return name

        # If we're using fallback location, we need to serve from there
        if self.location == "/tmp/media":
            # For now, return the media URL - we'll need to serve /tmp/media via Django
            return f"{self.base_url}{name}"

        return super().url(name)
