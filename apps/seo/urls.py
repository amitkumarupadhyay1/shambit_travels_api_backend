from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'data', views.SEODataViewSet, basename='seodata')
router.register(r'tools', views.SEOToolsViewSet, basename='seotools')

urlpatterns = [
    path('', include(router.urls)),
]

# Available endpoints:
# 
# SEO Data Management:
# GET /api/seo/data/ - List SEO data (with filtering)
# POST /api/seo/data/ - Create SEO data
# GET /api/seo/data/{id}/ - Get specific SEO data
# PUT /api/seo/data/{id}/ - Update SEO data
# PATCH /api/seo/data/{id}/ - Partial update SEO data
# DELETE /api/seo/data/{id}/ - Delete SEO data
#
# Custom SEO Data Actions:
# GET /api/seo/data/by_content_type/ - Get SEO data grouped by content type
# GET /api/seo/data/for_object/?content_type=app.model&object_id=123 - Get SEO for specific object
# GET /api/seo/data/{id}/meta_tags/?canonical_url=... - Generate HTML meta tags
# GET /api/seo/data/{id}/structured_data/ - Get structured data (JSON-LD)
# POST /api/seo/data/{id}/analyze/ - Analyze SEO data and get recommendations
# POST /api/seo/data/bulk_create/ - Create SEO data for multiple objects
# POST /api/seo/data/bulk_update/ - Update SEO data for multiple objects
# GET /api/seo/data/stats/ - Get SEO statistics
# GET /api/seo/data/missing_seo/?content_type=app.model - Find objects missing SEO
# POST /api/seo/data/generate_from_content/ - Auto-generate SEO from content
# GET /api/seo/data/content_types/ - Get available content types for SEO
#
# SEO Tools:
# POST /api/seo/tools/validate_structured_data/ - Validate structured data
# POST /api/seo/tools/generate_sitemap_data/ - Generate sitemap data
# GET /api/seo/tools/seo_health_check/ - Perform SEO health check
#
# Query parameters for list endpoint:
# ?content_type=app.model - Filter by content type
# ?object_id=123 - Filter by object ID
# ?search=text - Search in title, description, keywords