from articles.models import Article
from media_library.models import Media
from packages.models import Package
from rest_framework import serializers

from .models import City, Highlight, TravelTip


class CitySerializer(serializers.ModelSerializer):
    """Simple city serializer for list views"""

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

    def get_gallery(self, obj):
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(obj)
        media_items = Media.objects.filter(content_type=content_type, object_id=obj.id)
        return MediaSerializer(media_items, many=True).data
