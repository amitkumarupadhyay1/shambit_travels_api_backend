"""
Integration examples for the SEO system
These examples show how to integrate SEO with existing models
"""

from django.contrib.contenttypes.models import ContentType
from .services.seo_service import SEOService
from .utils import SEOAnalyzer, StructuredDataGenerator, SEOUtils

# Example 1: Auto-generate SEO for new articles
def article_integration_example():
    """
    Example of integrating SEO with article creation
    """
    from articles.models import Article
    
    def create_article_with_seo(title, content, city, author):
        # Create the article
        article = Article.objects.create(
            title=title,
            content=content,
            city=city,
            author=author,
            status='PUBLISHED'
        )
        
        # Auto-generate SEO data
        seo_data = SEOService.generate_seo_from_content('articles.article', article.id)
        
        return article, seo_data

# Example 2: Bulk SEO generation for existing content
def bulk_seo_generation_example():
    """
    Example of generating SEO for existing content in bulk
    """
    from articles.models import Article
    from packages.models import Package
    from cities.models import City
    
    # Find articles missing SEO
    missing_articles = SEOService.find_missing_seo_data('articles.article')
    print(f"Found {missing_articles['missing_seo']} articles missing SEO data")
    
    # Generate SEO for missing articles
    if missing_articles['missing_objects']:
        article_ids = [obj['id'] for obj in missing_articles['missing_objects']]
        
        # Generate SEO data for each article
        for article_id in article_ids:
            try:
                seo_data = SEOService.generate_seo_from_content('articles.article', article_id)
                print(f"Generated SEO for article {article_id}: {seo_data.title}")
            except Exception as e:
                print(f"Error generating SEO for article {article_id}: {e}")
    
    # Bulk create SEO for packages
    packages_without_seo = Package.objects.exclude(
        id__in=SEOData.objects.filter(
            content_type=ContentType.objects.get_for_model(Package)
        ).values_list('object_id', flat=True)
    )
    
    if packages_without_seo.exists():
        package_ids = list(packages_without_seo.values_list('id', flat=True))
        result = SEOService.bulk_create_seo_data(
            content_type='packages.package',
            object_ids=package_ids,
            seo_data={
                'title': 'Travel Package - Book Now',
                'description': 'Discover amazing travel experiences with our curated packages',
                'keywords': 'travel, package, vacation, booking'
            }
        )
        print(f"Bulk created SEO for {result['created_count']} packages")

# Example 3: SEO analysis and optimization
def seo_analysis_example():
    """
    Example of analyzing and optimizing SEO data
    """
    from .models import SEOData
    
    analyzer = SEOAnalyzer()
    
    # Analyze all SEO data
    poor_seo_entries = []
    
    for seo_data in SEOData.objects.all():
        analysis = analyzer.analyze_seo_data(seo_data)
        
        if analysis['overall_score'] in ['poor', 'fair']:
            poor_seo_entries.append({
                'seo_data': seo_data,
                'analysis': analysis,
                'object': seo_data.content_object
            })
    
    print(f"Found {len(poor_seo_entries)} SEO entries that need improvement")
    
    # Show recommendations for poor entries
    for entry in poor_seo_entries[:5]:  # Show first 5
        print(f"\nObject: {entry['object']}")
        print(f"Score: {entry['analysis']['overall_score']}")
        print("Recommendations:")
        for rec in entry['analysis']['recommendations']:
            print(f"  - {rec}")

# Example 4: Template integration
def template_integration_example():
    """
    Example of how to use SEO data in Django templates
    """
    from django.shortcuts import render, get_object_or_404
    from articles.models import Article
    from .models import SEOData
    
    def article_detail_view(request, slug):
        article = get_object_or_404(Article, slug=slug)
        
        # Get SEO data for the article
        try:
            seo_data = SEOData.objects.get(
                content_type=ContentType.objects.get_for_model(Article),
                object_id=article.id
            )
            
            # Generate meta tags HTML
            canonical_url = request.build_absolute_uri()
            meta_tags_html = SEOUtils.generate_meta_tags(seo_data, canonical_url)
            
            # Generate JSON-LD
            json_ld_html = SEOUtils.generate_json_ld(seo_data.structured_data)
            
        except SEOData.DoesNotExist:
            # Fallback SEO data
            seo_data = None
            meta_tags_html = f'<title>{article.title}</title><meta name="description" content="{article.content[:160]}">'
            json_ld_html = ''
        
        return render(request, 'articles/detail.html', {
            'article': article,
            'seo_data': seo_data,
            'meta_tags_html': meta_tags_html,
            'json_ld_html': json_ld_html
        })

# Example 5: API integration for frontend
def api_integration_example():
    """
    Example of using SEO API endpoints
    """
    import requests
    
    # Get SEO data for a specific article
    def get_article_seo(article_id):
        response = requests.get(
            f'/api/seo/data/for_object/',
            params={
                'content_type': 'articles.article',
                'object_id': article_id
            }
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    # Generate meta tags for frontend
    def get_meta_tags(seo_data_id, canonical_url):
        response = requests.get(
            f'/api/seo/data/{seo_data_id}/meta_tags/',
            params={'canonical_url': canonical_url}
        )
        
        if response.status_code == 200:
            return response.json()['meta_tags_html']
        return ''
    
    # Get structured data
    def get_structured_data(seo_data_id):
        response = requests.get(f'/api/seo/data/{seo_data_id}/structured_data/')
        
        if response.status_code == 200:
            return response.json()
        return {}

# Example 6: Custom SEO for different content types
def custom_seo_generation():
    """
    Example of custom SEO generation for different content types
    """
    from cities.models import City
    from packages.models import Package
    
    def generate_city_seo(city):
        """Generate SEO specifically for cities"""
        seo_data = {
            'title': f"Visit {city.name} - Travel Guide & Packages",
            'description': f"Discover {city.name} with our comprehensive travel guide. "
                          f"Find the best packages, attractions, and travel tips for {city.name}.",
            'keywords': f"{city.name}, travel, tourism, packages, attractions, guide",
            'og_title': f"Explore {city.name} - Amazing Travel Destination",
            'og_description': f"Plan your perfect trip to {city.name}. "
                             f"Discover attractions, book packages, and get travel tips."
        }
        
        # Generate structured data
        generator = StructuredDataGenerator()
        seo_data['structured_data'] = generator.generate_for_object(city)
        
        return SEOService.create_seo_data('cities.city', city.id, seo_data)
    
    def generate_package_seo(package):
        """Generate SEO specifically for packages"""
        seo_data = {
            'title': f"{package.name} - {package.city.name} Travel Package",
            'description': f"Book {package.name} in {package.city.name}. "
                          f"{package.description[:100]}... Book now for the best rates!",
            'keywords': f"{package.name}, {package.city.name}, travel package, booking, vacation",
            'og_title': f"Book {package.name} - {package.city.name}",
            'og_description': f"Experience {package.name} in {package.city.name}. "
                             f"Book your dream vacation package today!"
        }
        
        # Generate structured data
        generator = StructuredDataGenerator()
        seo_data['structured_data'] = generator.generate_for_object(package)
        
        return SEOService.create_seo_data('packages.package', package.id, seo_data)

# Example 7: SEO monitoring and maintenance
def seo_monitoring_example():
    """
    Example of SEO monitoring and maintenance tasks
    """
    def daily_seo_health_check():
        """Daily SEO health check"""
        health_report = SEOService.seo_health_check()
        
        if health_report['health_percentage'] < 80:
            print(f"⚠️  SEO Health Alert: {health_report['health_percentage']:.1f}%")
            print(f"Issues found: {health_report['error_count']} errors, {health_report['warning_count']} warnings")
            
            # Log top issues
            for issue in health_report['top_issues'][:3]:
                print(f"- {issue['object']}: {', '.join(issue['issues'][:2])}")
        else:
            print(f"✅ SEO Health Good: {health_report['health_percentage']:.1f}%")
    
    def weekly_seo_audit():
        """Weekly comprehensive SEO audit"""
        stats = SEOService.get_seo_stats()
        
        print("📊 Weekly SEO Report")
        print(f"Total SEO entries: {stats['total_seo_data']}")
        print(f"Complete basic SEO: {stats['completeness']['basic_seo_percentage']:.1f}%")
        print(f"With Open Graph: {stats['completeness']['og_percentage']:.1f}%")
        print(f"With Structured Data: {stats['completeness']['structured_data_percentage']:.1f}%")
        
        # Check for missing SEO data
        for ct_data in stats['by_content_type']:
            content_type = f"{ct_data['content_type__app_label']}.{ct_data['content_type__model']}"
            try:
                missing_info = SEOService.find_missing_seo_data(content_type)
                if missing_info['missing_seo'] > 0:
                    print(f"⚠️  {content_type}: {missing_info['missing_seo']} objects missing SEO")
            except:
                pass

# Example 8: Integration with content management workflow
def content_workflow_integration():
    """
    Example of integrating SEO into content management workflow
    """
    from articles.models import Article
    
    def publish_article_with_seo_check(article_id):
        """Publish article only if SEO is complete"""
        article = Article.objects.get(id=article_id)
        
        # Check if SEO data exists
        try:
            seo_data = SEOData.objects.get(
                content_type=ContentType.objects.get_for_model(Article),
                object_id=article.id
            )
            
            # Analyze SEO quality
            analyzer = SEOAnalyzer()
            analysis = analyzer.analyze_seo_data(seo_data)
            
            if analysis['overall_score'] in ['poor']:
                return {
                    'success': False,
                    'message': 'Article SEO needs improvement before publishing',
                    'recommendations': analysis['recommendations']
                }
            
        except SEOData.DoesNotExist:
            # Auto-generate SEO data
            seo_data = SEOService.generate_seo_from_content('articles.article', article.id)
        
        # Publish the article
        article.status = 'PUBLISHED'
        article.save()
        
        return {
            'success': True,
            'message': 'Article published successfully',
            'seo_score': analysis['overall_score'] if 'analysis' in locals() else 'generated'
        }

if __name__ == '__main__':
    # These are just examples - don't run directly
    print("SEO system integration examples")
    print("See the functions above for implementation details")