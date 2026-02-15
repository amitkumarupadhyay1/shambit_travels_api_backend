"""
Search result serializers for universal search
"""

from rest_framework import serializers


class BaseSearchResultSerializer(serializers.Serializer):
    """Base serializer for all search results"""

    id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    excerpt = serializers.CharField()
    slug = serializers.SlugField()
    url = serializers.CharField()
    image = serializers.CharField(allow_null=True)
    relevance_score = serializers.FloatField()
    content_type = serializers.CharField()
    breadcrumb = serializers.CharField()


class PackageSearchSerializer(serializers.Serializer):
    """Serializer for package search results"""

    id = serializers.IntegerField()
    type = serializers.SerializerMethodField()
    title = serializers.CharField(source="name")
    description = serializers.CharField()
    excerpt = serializers.SerializerMethodField()
    slug = serializers.SlugField()
    url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    price = serializers.DecimalField(
        source="base_price", max_digits=10, decimal_places=2
    )
    duration = serializers.SerializerMethodField()
    relevance_score = serializers.FloatField(source="rank")
    content_type = serializers.SerializerMethodField()
    breadcrumb = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "package"

    def get_excerpt(self, obj):
        """Generate excerpt with query highlighting"""
        query = self.context.get("query", "")
        description = obj.description[:200] if obj.description else ""

        # Simple highlighting - wrap query matches in <mark> tags
        if query and description:
            import re

            # Case-insensitive replacement
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            description = pattern.sub(f"<mark>{query}</mark>", description)

        return description + "..." if description else ""

    def get_url(self, obj):
        return f"/packages/{obj.slug}"

    def get_image(self, obj):
        """Get featured image from media library"""
        try:
            if hasattr(obj, "media") and obj.media.exists():
                return obj.media.first().file_url
        except Exception:
            pass
        return None

    def get_duration(self, obj):
        """Get package duration"""
        if hasattr(obj, "duration_days") and obj.duration_days:
            return f"{obj.duration_days} days"
        return None

    def get_content_type(self, obj):
        return "package"

    def get_breadcrumb(self, obj):
        return "Packages > Travel Packages"


class CitySearchSerializer(serializers.Serializer):
    """Serializer for city search results"""

    id = serializers.IntegerField()
    type = serializers.SerializerMethodField()
    title = serializers.CharField(source="name")
    description = serializers.CharField()
    excerpt = serializers.SerializerMethodField()
    slug = serializers.SlugField()
    url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    relevance_score = serializers.FloatField(source="rank")
    content_type = serializers.SerializerMethodField()
    breadcrumb = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "city"

    def get_excerpt(self, obj):
        """Generate excerpt with query highlighting"""
        query = self.context.get("query", "")
        description = obj.description[:200] if obj.description else ""

        if query and description:
            import re

            pattern = re.compile(re.escape(query), re.IGNORECASE)
            description = pattern.sub(f"<mark>{query}</mark>", description)

        return description + "..." if description else ""

    def get_url(self, obj):
        return f"/cities/{obj.slug}"

    def get_image(self, obj):
        """Get hero image"""
        if hasattr(obj, "hero_image") and obj.hero_image:
            return (
                obj.hero_image.url
                if hasattr(obj.hero_image, "url")
                else str(obj.hero_image)
            )
        return None

    def get_content_type(self, obj):
        return "city"

    def get_breadcrumb(self, obj):
        return "Cities > Destinations"


class ArticleSearchSerializer(serializers.Serializer):
    """Serializer for article search results"""

    id = serializers.IntegerField()
    type = serializers.SerializerMethodField()
    title = serializers.CharField()
    excerpt = serializers.SerializerMethodField()
    slug = serializers.SlugField()
    url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    author = serializers.CharField()
    published_date = serializers.DateTimeField(source="created_at")
    relevance_score = serializers.FloatField(source="rank")
    content_type = serializers.SerializerMethodField()
    breadcrumb = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "article"

    def get_excerpt(self, obj):
        """Generate excerpt with query highlighting"""
        query = self.context.get("query", "")
        # Try to get excerpt from content
        content = obj.content[:200] if hasattr(obj, "content") and obj.content else ""

        if query and content:
            import re

            pattern = re.compile(re.escape(query), re.IGNORECASE)
            content = pattern.sub(f"<mark>{query}</mark>", content)

        return content + "..." if content else ""

    def get_url(self, obj):
        return f"/articles/{obj.slug}"

    def get_image(self, obj):
        """Get featured image"""
        if hasattr(obj, "featured_image") and obj.featured_image:
            return (
                obj.featured_image.url
                if hasattr(obj.featured_image, "url")
                else str(obj.featured_image)
            )
        return None

    def get_content_type(self, obj):
        return "article"

    def get_breadcrumb(self, obj):
        return "Articles > Travel Guides"


class ExperienceSearchSerializer(serializers.Serializer):
    """Serializer for experience search results"""

    id = serializers.IntegerField()
    type = serializers.SerializerMethodField()
    title = serializers.CharField(source="name")
    description = serializers.CharField()
    excerpt = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    relevance_score = serializers.FloatField(source="rank")
    content_type = serializers.SerializerMethodField()
    breadcrumb = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "experience"

    def get_excerpt(self, obj):
        """Generate excerpt with query highlighting"""
        query = self.context.get("query", "")
        description = obj.description[:200] if obj.description else ""

        if query and description:
            import re

            pattern = re.compile(re.escape(query), re.IGNORECASE)
            description = pattern.sub(f"<mark>{query}</mark>", description)

        return description + "..." if description else ""

    def get_slug(self, obj):
        """Generate slug from name"""
        if hasattr(obj, "slug"):
            return obj.slug
        # Fallback: generate from name
        from django.utils.text import slugify

        return slugify(obj.name)

    def get_url(self, obj):
        slug = self.get_slug(obj)
        return f"/experiences/{slug}"

    def get_image(self, obj):
        """Get experience image"""
        try:
            if hasattr(obj, "media") and obj.media.exists():
                return obj.media.first().file_url
        except Exception:
            pass
        return None

    def get_content_type(self, obj):
        return "experience"

    def get_breadcrumb(self, obj):
        return "Experiences > Activities"
