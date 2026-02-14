import logging

from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from .models import Media
from .services.media_service import MediaService

logger = logging.getLogger(__name__)


def _invalidate_media_related_caches() -> None:
    """
    Invalidate cached responses that embed media URLs.
    """
    try:
        from packages.cache import invalidate_cache

        patterns = [
            "packages:*",
            "package:*",
            "experiences:*",
            "experience:*",
            # Legacy prefixes kept for compatibility with older keys
            "api:packages:*",
            "api:package:*",
            "api:experiences:*",
            "api:experience:*",
        ]
        for pattern in patterns:
            invalidate_cache(pattern)
    except Exception as exc:
        logger.warning("Failed to invalidate media-related caches: %s", exc)


@receiver(pre_save, sender=Media)
def delete_previous_file_on_replace(sender, instance: Media, **kwargs):
    """
    If a Media file is replaced, remove the old file from storage/cloudinary.
    """
    if not instance.pk:
        return

    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    previous_name = previous.file.name if previous.file else None
    current_name = instance.file.name if instance.file else None

    if previous_name and previous_name != current_name:
        MediaService.delete_media_file(previous)


@receiver(pre_delete, sender=Media)
def delete_media_file_on_delete(sender, instance: Media, **kwargs):
    """
    Ensure the storage object and Cloudinary asset are removed before DB delete.
    """
    MediaService.delete_media_file(instance)


@receiver(post_save, sender=Media)
def invalidate_media_cache_on_save(sender, instance: Media, **kwargs):
    _invalidate_media_related_caches()


@receiver(post_delete, sender=Media)
def invalidate_media_cache_on_delete(sender, instance: Media, **kwargs):
    _invalidate_media_related_caches()
