from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from articles.models import Article
from media_library.models import Media
from packages.models import Package
from rest_framework import serializers

from .models import City, Highlight, TravelTip


class CitySerializer(serializers.ModelSerializer):
    """Simple city serializer for list views"""

    hero_image = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "hero_image",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]

    def get_hero_image(self, obj):
        if not obj.hero_image:
            return None
        return self._append_cache_buster(obj.hero_image.url, obj.updated_at)

    def _append_cache_buster(self, url: str, version_source) -> str:
        if not url or not version_source:
            return url

        timestamp = int(version_source.timestamp())
        parts = urlsplit(url)
        query_params = dict(parse_qsl(parts.query))
        query_params["v"] = str(timestamp)

        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(query_params),
                parts.fragment,
            )
        )


class HighlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Highlight
        fields = ["title", "description", "icon"]


class TravelTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelTip
        fields = ["title", "content"]


class ArticleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["title", "slug", "author", "created_at"]


class PackageSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ["name", "slug", "description"]


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ["file", "alt_text", "title"]


class CityContextSerializer(serializers.ModelSerializer):
    highlights = HighlightSerializer(many=True, read_only=True)
    travel_tips = TravelTipSerializer(many=True, read_only=True)
    articles = ArticleSummarySerializer(many=True, read_only=True)
    packages = PackageSummarySerializer(many=True, read_only=True)

    # Generic media gallery
    gallery = serializers.SerializerMethodField()
    hero_image = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = [
            "name",
            "slug",
            "description",
            "hero_image",
            "highlights",
            "travel_tips",
            "articles",
            "packages",
            "gallery",
            "meta_title",
            "meta_description",
        ]

    def get_hero_image(self, obj):
        if not obj.hero_image:
            return None
        return self._append_cache_buster(obj.hero_image.url, obj.updated_at)

    def get_gallery(self, obj):
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(obj)
        media_items = Media.objects.filter(content_type=content_type, object_id=obj.id)
        return MediaSerializer(media_items, many=True).data

    def _append_cache_buster(self, url: str, version_source) -> str:
        if not url or not version_source:
            return url

        timestamp = int(version_source.timestamp())
        parts = urlsplit(url)
        query_params = dict(parse_qsl(parts.query))
        query_params["v"] = str(timestamp)

        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(query_params),
                parts.fragment,
            )
        )
