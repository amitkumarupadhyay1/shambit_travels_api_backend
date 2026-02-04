# SEO App

A comprehensive SEO management system for the travel platform with production-level features for managing meta tags, Open Graph data, and structured data.

## Features

### Core Functionality
- ✅ Generic SEO data management for any content type
- ✅ Meta tags generation (title, description, keywords)
- ✅ Open Graph data for social media sharing
- ✅ Structured data (JSON-LD) generation
- ✅ SEO analysis and recommendations
- ✅ Bulk operations for efficiency
- ✅ Content type filtering and search

### API Endpoints

#### SEO Data Management
- `GET /api/seo/data/` - List SEO data (with filtering)
- `POST /api/seo/data/` - Create SEO data
- `GET /api/seo/data/{id}/` - Get specific SEO data
- `PUT /api/seo/data/{id}/` - Update SEO data
- `PATCH /api/seo/data/{id}/` - Partial update SEO data
- `DELETE /api/seo/data/{id}/` - Delete SEO data

#### Custom SEO Actions
- `GET /api/seo/data/by_content_type/` - Get SEO data grouped by content type
- `GET /api/seo/data/for_object/?content_type=app.model&object_id=123` - Get SEO for specific object
- `GET /api/seo/data/{id}/meta_tags/?canonical_url=...` - Generate HTML meta tags
- `GET /api/seo/data/{id}/structured_data/` - Get structured data (JSON-LD)
- `POST /api/seo/data/{id}/analyze/` - Analyze SEO data and get recommendations
- `POST /api/seo/data/bulk_create/` - Create SEO data for multiple objects
- `POST /api/seo/data/bulk_update/` - Update SEO data for multiple objects
- `GET /api/seo/data/stats/` - Get SEO statistics
- `GET /api/seo/data/missing_seo/?content_type=app.model` - Find objects missing SEO
- `POST /api/seo/data/generate_from_content/` - Auto-generate SEO from content
- `GET /api/seo/data/content_types/` - Get available content types for SEO

#### SEO Tools
- `POST /api/seo/tools/validate_structured_data/` - Validate structured data
- `POST /api/seo/tools/generate_sitemap_data/` - Generate sitemap data
- `GET /api/seo/tools/seo_health_check/` - Perform SEO health check

#### Query Parameters for List Endpoint
- `?content_type=app.model` - Filter by content type
- `?object_id=123` - Filter by object ID
- `?search=text` - Search in title, description, keywords

### Service Layer

The `SEOService` class provides business logic methods:

```python
from seo.services.seo_service import SEOService

# Create SEO data for an object
seo_data = SEOService.create_seo_data(
    content_type='articles.article',
    object_id=123,
    seo_data={
        'title': 'Amazing Travel Destination',
        'description': 'Discover the beauty of this amazing destination',
        'keywords': 'travel, destination, vacation'
    }
)

# Auto-generate SEO data from content
seo_data = SEOService.generate_seo_from_content('packages.package', 456)

# Bulk create SEO data
result = SEOService.bulk_create_seo_data(
    content_type='cities.city',
    object_ids=[1, 2, 3, 4, 5],
    seo_data={
        'title': 'Visit {city_name}',
        'description': 'Explore the wonders of {city_name}'
    }
)

# Get SEO statistics
stats = SEOService.get_seo_stats()
# Returns: {'total_seo_data': 150, 'by_content_type': [...], 'completeness': {...}}

# Find missing SEO data
missing = SEOService.find_missing_seo_data('articles.article')
# Returns: {'missing_seo': 25, 'missing_objects': [...]}
```

### SEO Analysis and Recommendations

The system provides comprehensive SEO analysis:

```python
from seo.utils import SEOAnalyzer

analyzer = SEOAnalyzer()
analysis = analyzer.analyze_seo_data(seo_data)

# Returns analysis with:
# - title_score: 'good', 'too_short', 'too_long', 'missing'
# - description_score: 'good', 'too_short', 'too_long', 'missing'  
# - keywords_score: 'good', 'too_few', 'too_many', 'missing'
# - og_completeness: 0.0 to 1.0 (percentage)
# - overall_score: 'excellent', 'good', 'fair', 'poor'
# - recommendations: List of specific improvement suggestions
```

### Structured Data Generation

Automatic structured data generation for different content types:

```python
from seo.utils import StructuredDataGenerator

generator = StructuredDataGenerator()

# Generate Article schema for articles
article_schema = generator.generate_for_object(article)
# Returns JSON-LD with Article schema

# Generate Product schema for packages
package_schema = generator.generate_for_object(package)
# Returns JSON-LD with Product schema

# Generate TouristDestination schema for cities
city_schema = generator.generate_for_object(city)
# Returns JSON-LD with TouristDestination schema
```

### Management Commands

#### Generate SEO Data
```bash
# Generate SEO for all articles missing it
python manage.py generate_seo articles.article

# Generate for specific objects
python manage.py generate_seo packages.package --object-ids 1 2 3

# Dry run to see what would be generated
python manage.py generate_seo cities.city --dry-run

# Overwrite existing SEO data
python manage.py generate_seo articles.article --overwrite
```

#### SEO Audit
```bash
# Perform comprehensive SEO audit
python manage.py seo_audit

# Audit specific content type
python manage.py seo_audit --content-type articles.article

# Detailed analysis
python manage.py seo_audit --detailed

# Export report to CSV
python manage.py seo_audit --export seo_report.csv
```

### Admin Interface

Enhanced admin interface with:
- **SEO Score Visualization**: Color-coded SEO scores for each entry
- **Completeness Indicators**: Visual indicators for Open Graph and structured data
- **Bulk Actions**: Analyze SEO, generate missing data, regenerate structured data
- **SEO Dashboard**: Comprehensive overview of SEO health
- **Bulk Generate Tool**: Generate SEO data for multiple objects at once

### Database Model

The SEO system uses a generic foreign key to attach SEO data to any model:

```python
class SEOData(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Basic SEO
    title = models.CharField(max_length=255)
    description = models.TextField()
    keywords = models.CharField(max_length=255, blank=True)
    
    # Open Graph
    og_title = models.CharField(max_length=255, blank=True)
    og_description = models.TextField(blank=True)
    og_image = models.ImageField(upload_to='seo/', null=True, blank=True)
    
    # Structured Data
    structured_data = models.JSONField(null=True, blank=True)
```

### Usage Examples

#### Frontend Integration
```javascript
// Get SEO data for a specific object
const response = await fetch('/api/seo/data/for_object/?content_type=articles.article&object_id=123');
const seoData = await response.json();

// Generate meta tags HTML
const metaResponse = await fetch(`/api/seo/data/${seoData.id}/meta_tags/?canonical_url=${window.location.href}`);
const metaTags = await metaResponse.json();

// Insert meta tags into page head
document.head.insertAdjacentHTML('beforeend', metaTags.meta_tags_html);

// Get structured data
const structuredResponse = await fetch(`/api/seo/data/${seoData.id}/structured_data/`);
const structuredData = await structuredResponse.json();

// Insert JSON-LD script
const script = document.createElement('script');
script.type = 'application/ld+json';
script.textContent = JSON.stringify(structuredData);
document.head.appendChild(script);
```

#### Backend Integration
```python
# In your views, automatically create SEO data
from seo.services.seo_service import SEOService

def create_article(request):
    article = Article.objects.create(...)
    
    # Auto-generate SEO data
    SEOService.generate_seo_from_content('articles.article', article.id)
    
    return JsonResponse({'success': True})

# In templates, use SEO data
def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    
    try:
        seo_data = SEOData.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            object_id=article.id
        )
    except SEOData.DoesNotExist:
        seo_data = None
    
    return render(request, 'article_detail.html', {
        'article': article,
        'seo_data': seo_data
    })
```

### Performance Considerations

1. **Database Optimization**: Uses generic foreign keys efficiently
2. **Bulk Operations**: Supports bulk create/update for large datasets
3. **Caching**: Consider caching frequently accessed SEO data
4. **Lazy Loading**: Structured data generated on-demand
5. **Pagination**: All list endpoints are paginated

### SEO Best Practices Implemented

1. **Title Optimization**: 30-60 character recommendations
2. **Meta Description**: 120-160 character recommendations  
3. **Keywords**: 3-10 keyword recommendations
4. **Open Graph**: Complete OG tag support
5. **Structured Data**: Schema.org compliant JSON-LD
6. **Canonical URLs**: Support for canonical URL specification
7. **Twitter Cards**: Automatic Twitter Card meta tags

### Content Type Support

The system supports SEO for:
- **Articles**: Article schema with author and publication data
- **Packages**: Product schema with pricing and location
- **Cities**: TouristDestination schema with attractions
- **Any Model**: Generic Thing schema as fallback

### Future Enhancements

- XML sitemap generation
- SEO performance tracking
- A/B testing for meta tags
- Integration with Google Search Console
- Automated SEO monitoring and alerts
- Multi-language SEO support