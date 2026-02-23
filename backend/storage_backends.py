"""
Custom storage backends for Railway deployment
"""

import os

from django.core.files.storage import FileSystemStorage


class RailwayFileSystemStorage(FileSystemStorage):
    """
    Custom file system storage that handles Railway volume permissions
    """

    def _save(self, name, content):
        """
        Override _save to handle permission issues on Railway volumes
        """
        print(f"🔄 Attempting to save file: {name}")
        print(f"📁 Storage location: {self.location}")

        # Try the normal save first
        try:
            saved_name = super()._save(name, content)
            full_path = self.path(saved_name)
            print(f"✅ Successfully saved to: {full_path}")
            print(f"📁 File exists: {os.path.exists(full_path)}")
            return saved_name
        except PermissionError as e:
            print(f"⚠️ Permission denied saving {name}: {e}")

            # Fallback: use /tmp directory which is always writable
            fallback_root = "/tmp/media"
            os.makedirs(fallback_root, exist_ok=True)

            # Create a new storage instance pointing to /tmp
            fallback_storage = FileSystemStorage(location=fallback_root)

            # Save to fallback location
            saved_name = fallback_storage._save(name, content)
            fallback_path = os.path.join(fallback_root, saved_name)
            print(f"📁 Saved to fallback location: {fallback_path}")
            print(f"📁 Fallback file exists: {os.path.exists(fallback_path)}")

            # Update our location to the fallback for future operations
            self.location = fallback_root

            return saved_name

    def url(self, name):
        """
        Generate URL for the file
        """
        if not name:
            return name

        # Always use the standard media URL - our custom view will handle the lookup
        url = f"/media/{name}"
        print(f"🔗 Generated URL for {name}: {url}")
        return url
