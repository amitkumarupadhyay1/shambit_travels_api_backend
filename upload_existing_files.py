"""
Upload all files from backend/media/library to Cloudinary
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from pathlib import Path

import cloudinary
import cloudinary.api
import cloudinary.uploader


def upload_all_local_files():
    """Upload all files from media/library to Cloudinary"""

    from django.conf import settings

    media_dir = Path(settings.BASE_DIR) / "media" / "library"

    if not media_dir.exists():
        print(f"❌ Directory not found: {media_dir}")
        return

    # Get all files (not directories)
    files = [f for f in media_dir.iterdir() if f.is_file()]

    print(f"Found {len(files)} files in {media_dir}\n")

    success_count = 0
    error_count = 0

    for file_path in files:
        try:
            print(f"📤 Uploading: {file_path.name}")

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                str(file_path),
                folder="media/library",
                public_id=file_path.stem,  # filename without extension
                resource_type="auto",
                overwrite=True,
            )

            print(f"   ✅ Uploaded to: {result['secure_url']}")
            print(f"   Public ID: {result['public_id']}\n")

            success_count += 1

        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            error_count += 1

    print(f"\n{'='*50}")
    print(f"Upload complete!")
    print(f"✅ Success: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"{'='*50}")

    # Verify uploads
    print("\n🔍 Verifying uploads on Cloudinary...")
    try:
        resources = cloudinary.api.resources(
            type="upload", prefix="media/library", max_results=100
        )
        print(f"✅ Found {len(resources['resources'])} files in media/library folder")
        for r in resources["resources"]:
            print(f"   - {r['public_id']}")
    except Exception as e:
        print(f"❌ Error verifying: {e}")


if __name__ == "__main__":
    upload_all_local_files()
