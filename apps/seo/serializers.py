from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from .models import SEOData


class SEODataSerializer(serializers.ModelSerializer):
    """
    Full SEO data serializer for detailed views
    """

    content_type_name = serializers.CharField(
        source="content_type.model", read_only=True
    )
    content_object_str = serializers.CharField(
        source="content_object.__str__", read_only=True
    )

    class Meta:
        model = SEOData
        fields = [
            "id",
            "content_type",
            "object_id",
            "content_type_name",
            "content_object_str",
            "title",
            "description",
            "keywords",
            "og_title",
            "og_description",
            "og_image",
            "structured_data",
        ]
        read_only_fields = ["id", "content_type_name", "content_object_str"]


class SEODataListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views
    """

    content_type_name = serializers.CharField(
        source="content_type.model", read_only=True
    )
    content_object_str = serializers.CharField(
        source="content_object.__str__", read_only=True
    )

    class Meta:
        model = SEOData
        fields = [
            "id",
            "content_type_name",
            "content_object_str",
            "title",
            "description",
            "keywords",
        ]


class SEODataCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating SEO data
    """

    class Meta:
        model = SEOData
        fields = [
            "content_type",
            "object_id",
            "title",
            "description",
            "keywords",
            "og_title",
            "og_description",
            "og_image",
            "structured_data",
        ]

    def validate(self, data):
        """
        Validate that the content object exists
        """
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        if content_type and object_id:
            try:
                content_type.get_object_for_this_type(id=object_id)
            except content_type.model_class().DoesNotExist:
                raise serializers.ValidationError(
                    f"Object with id {object_id} does not exist for {content_type.model}"
                )

        return data


class SEODataUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating SEO data (excluding content_type and object_id)
    """

    class Meta:
        model = SEOData
        fields = [
            "title",
            "description",
            "keywords",
            "og_title",
            "og_description",
            "og_image",
            "structured_data",
        ]


class ContentTypeSEOSerializer(serializers.ModelSerializer):
    """
    Serializer for getting SEO data by content type
    """

    seo_data = SEODataListSerializer(source="seodata_set", many=True, read_only=True)

    class Meta:
        model = ContentType
        fields = ["id", "app_label", "model", "seo_data"]


class SEOMetaTagsSerializer(serializers.Serializer):
    """
    Serializer for generating HTML meta tags
    """

    title = serializers.CharField()
    description = serializers.CharField()
    keywords = serializers.CharField(required=False, allow_blank=True)
    og_title = serializers.CharField(required=False, allow_blank=True)
    og_description = serializers.CharField(required=False, allow_blank=True)
    og_image = serializers.ImageField(required=False, allow_null=True)
    canonical_url = serializers.URLField(required=False, allow_blank=True)

    def to_representation(self, instance):
        """
        Convert to HTML meta tags format
        """
        data = super().to_representation(instance)

        meta_tags = []

        # Basic meta tags
        if data.get("title"):
            meta_tags.append(f'<title>{data["title"]}</title>')
            meta_tags.append(f'<meta name="title" content="{data["title"]}">')

        if data.get("description"):
            meta_tags.append(
                f'<meta name="description" content="{data["description"]}">'
            )

        if data.get("keywords"):
            meta_tags.append(f'<meta name="keywords" content="{data["keywords"]}">')

        # Open Graph tags
        og_title = data.get("og_title") or data.get("title")
        if og_title:
            meta_tags.append(f'<meta property="og:title" content="{og_title}">')

        og_description = data.get("og_description") or data.get("description")
        if og_description:
            meta_tags.append(
                f'<meta property="og:description" content="{og_description}">'
            )

        if data.get("og_image"):
            meta_tags.append(f'<meta property="og:image" content="{data["og_image"]}">')

        meta_tags.append('<meta property="og:type" content="website">')

        # Canonical URL
        if data.get("canonical_url"):
            meta_tags.append(f'<link rel="canonical" href="{data["canonical_url"]}">')

        return {"meta_tags": meta_tags, "meta_tags_html": "\n".join(meta_tags)}


class StructuredDataSerializer(serializers.Serializer):
    """
    Serializer for structured data (JSON-LD)
    """

    schema_type = serializers.CharField()
    data = serializers.JSONField()

    def validate_schema_type(self, value):
        """
        Validate schema type against common Schema.org types
        """
        valid_types = [
            "Article",
            "BlogPosting",
            "NewsArticle",
            "WebPage",
            "WebSite",
            "Organization",
            "LocalBusiness",
            "TravelAgency",
            "TouristDestination",
            "TouristAttraction",
            "Hotel",
            "Restaurant",
            "Event",
            "Product",
            "Service",
            "Review",
            "Rating",
            "BreadcrumbList",
        ]

        if value not in valid_types:
            raise serializers.ValidationError(
                f"Schema type must be one of: {', '.join(valid_types)}"
            )

        return value


class SEOAnalysisSerializer(serializers.Serializer):
    """
    Serializer for SEO analysis results
    """

    title_length = serializers.IntegerField()
    title_score = serializers.CharField()
    description_length = serializers.IntegerField()
    description_score = serializers.CharField()
    keywords_count = serializers.IntegerField()
    keywords_score = serializers.CharField()
    og_completeness = serializers.FloatField()
    overall_score = serializers.CharField()
    recommendations = serializers.ListField(child=serializers.CharField())


class BulkSEOSerializer(serializers.Serializer):
    """
    Serializer for bulk SEO operations
    """

    content_type = serializers.CharField()
    object_ids = serializers.ListField(child=serializers.IntegerField())
    seo_data = serializers.DictField()

    def validate_content_type(self, value):
        """
        Validate content type format (app_label.model)
        """
        try:
            app_label, model = value.split(".")
            ContentType.objects.get(app_label=app_label, model=model)
        except (ValueError, ContentType.DoesNotExist):
            raise serializers.ValidationError(
                "Content type must be in format 'app_label.model' and must exist"
            )
        return value
