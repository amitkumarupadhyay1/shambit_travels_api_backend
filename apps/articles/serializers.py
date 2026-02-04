from rest_framework import serializers
from .models import Article

class ArticleListSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'author', 'city_name',
            'meta_title', 'meta_description', 'created_at', 'updated_at'
        ]

    def get_excerpt(self, obj):
        # Return first 200 characters of content
        return obj.content[:200] + '...' if len(obj.content) > 200 else obj.content

class ArticleSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    city_slug = serializers.CharField(source='city.slug', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'author', 'city_name', 'city_slug',
            'meta_title', 'meta_description', 'created_at', 'updated_at'
        ]