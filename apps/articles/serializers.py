from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Article


class ArticleListSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    excerpt = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "author",
            "city_name",
            "featured_image",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_excerpt(self, obj) -> str:
        # Return first 200 characters of content
        return obj.content[:200] + "..." if len(obj.content) > 200 else obj.content

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_featured_image(self, obj) -> Optional[str]:
        if not obj.featured_image:
            return None
        return self._append_cache_buster(obj.featured_image.url, obj.updated_at)

    def _append_cache_buster(self, url: str, version_source) -> str:
        if not url or not version_source:
            return url

        # Skip cache-busting for Cloudinary URLs - they have their own versioning
        if "cloudinary.com" in url:
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


class ArticleSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    city_slug = serializers.CharField(source="city.slug", read_only=True)
    featured_image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "author",
            "city_name",
            "city_slug",
            "featured_image",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_featured_image(self, obj) -> Optional[str]:
        if not obj.featured_image:
            return None
        return self._append_cache_buster(obj.featured_image.url, obj.updated_at)

    def _append_cache_buster(self, url: str, version_source) -> str:
        if not url or not version_source:
            return url

        # Skip cache-busting for Cloudinary URLs - they have their own versioning
        if "cloudinary.com" in url:
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
