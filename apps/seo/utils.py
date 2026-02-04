from typing import Dict, List, Any
from django.utils import timezone
from .models import SEOData

class SEOAnalyzer:
    """
    Utility class for analyzing SEO data and providing recommendations
    """
    
    def analyze_seo_data(self, seo_data: SEOData) -> Dict[str, Any]:
        """
        Analyze SEO data and provide comprehensive recommendations
        """
        analysis = {
            'title_length': len(seo_data.title),
            'title_score': self._analyze_title(seo_data.title),
            'description_length': len(seo_data.description),
            'description_score': self._analyze_description(seo_data.description),
            'keywords_count': len(seo_data.keywords.split(',')) if seo_data.keywords else 0,
            'keywords_score': self._analyze_keywords(seo_data.keywords),
            'og_completeness': self._analyze_og_completeness(seo_data),
            'recommendations': []
        }
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(seo_data, analysis)
        
        # Calculate overall score
        analysis['overall_score'] = self._calculate_overall_score(analysis)
        
        return analysis
    
    def _analyze_title(self, title: str) -> str:
        """
        Analyze title and return score
        """
        if not title:
            return 'missing'
        
        length = len(title)
        if length < 30:
            return 'too_short'
        elif length > 60:
            return 'too_long'
        else:
            return 'good'
    
    def _analyze_description(self, description: str) -> str:
        """
        Analyze meta description and return score
        """
        if not description:
            return 'missing'
        
        length = len(description)
        if length < 120:
            return 'too_short'
        elif length > 160:
            return 'too_long'
        else:
            return 'good'
    
    def _analyze_keywords(self, keywords: str) -> str:
        """
        Analyze keywords and return score
        """
        if not keywords:
            return 'missing'
        
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        count = len(keyword_list)
        
        if count < 3:
            return 'too_few'
        elif count > 10:
            return 'too_many'
        else:
            return 'good'
    
    def _analyze_og_completeness(self, seo_data: SEOData) -> float:
        """
        Analyze Open Graph completeness (0-1 scale)
        """
        og_fields = ['og_title', 'og_description', 'og_image']
        completed_fields = 0
        
        for field in og_fields:
            value = getattr(seo_data, field)
            if value:
                completed_fields += 1
        
        return completed_fields / len(og_fields)
    
    def _generate_recommendations(self, seo_data: SEOData, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate specific recommendations based on analysis
        """
        recommendations = []
        
        # Title recommendations
        if analysis['title_score'] == 'missing':
            recommendations.append('Add a title tag - it\'s essential for SEO')
        elif analysis['title_score'] == 'too_short':
            recommendations.append('Title is too short - aim for 30-60 characters')
        elif analysis['title_score'] == 'too_long':
            recommendations.append('Title is too long - keep it under 60 characters')
        
        # Description recommendations
        if analysis['description_score'] == 'missing':
            recommendations.append('Add a meta description to improve click-through rates')
        elif analysis['description_score'] == 'too_short':
            recommendations.append('Meta description is too short - aim for 120-160 characters')
        elif analysis['description_score'] == 'too_long':
            recommendations.append('Meta description is too long - keep it under 160 characters')
        
        # Keywords recommendations
        if analysis['keywords_score'] == 'missing':
            recommendations.append('Add relevant keywords to help with search visibility')
        elif analysis['keywords_score'] == 'too_few':
            recommendations.append('Add more keywords - aim for 3-10 relevant terms')
        elif analysis['keywords_score'] == 'too_many':
            recommendations.append('Too many keywords - focus on 3-10 most relevant terms')
        
        # Open Graph recommendations
        if analysis['og_completeness'] < 0.5:
            recommendations.append('Improve Open Graph data for better social media sharing')
        
        if not seo_data.og_image:
            recommendations.append('Add an Open Graph image for social media previews')
        
        if not seo_data.structured_data:
            recommendations.append('Add structured data (JSON-LD) to help search engines understand your content')
        
        return recommendations
    
    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> str:
        """
        Calculate overall SEO score
        """
        score = 0
        max_score = 4
        
        # Title score
        if analysis['title_score'] == 'good':
            score += 1
        elif analysis['title_score'] in ['too_short', 'too_long']:
            score += 0.5
        
        # Description score
        if analysis['description_score'] == 'good':
            score += 1
        elif analysis['description_score'] in ['too_short', 'too_long']:
            score += 0.5
        
        # Keywords score
        if analysis['keywords_score'] == 'good':
            score += 1
        elif analysis['keywords_score'] in ['too_few', 'too_many']:
            score += 0.5
        
        # Open Graph completeness
        score += analysis['og_completeness']
        
        percentage = (score / max_score) * 100
        
        if percentage >= 90:
            return 'excellent'
        elif percentage >= 75:
            return 'good'
        elif percentage >= 50:
            return 'fair'
        else:
            return 'poor'

class StructuredDataGenerator:
    """
    Utility class for generating structured data (JSON-LD)
    """
    
    def generate_for_object(self, obj) -> Dict[str, Any]:
        """
        Generate structured data based on object type
        """
        if hasattr(obj, '_meta'):
            model_name = obj._meta.model_name
            
            if model_name == 'article':
                return self._generate_article_schema(obj)
            elif model_name == 'package':
                return self._generate_package_schema(obj)
            elif model_name == 'city':
                return self._generate_city_schema(obj)
            else:
                return self._generate_generic_schema(obj)
        
        return {}
    
    def _generate_article_schema(self, article) -> Dict[str, Any]:
        """
        Generate Article schema for articles
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article.title,
            "description": getattr(article, 'meta_description', article.content[:200]),
            "author": {
                "@type": "Person",
                "name": getattr(article, 'author', 'Travel Platform')
            },
            "publisher": {
                "@type": "Organization",
                "name": "Travel Platform"
            },
            "datePublished": article.created_at.isoformat() if hasattr(article, 'created_at') else None,
            "dateModified": article.updated_at.isoformat() if hasattr(article, 'updated_at') else None
        }
        
        if hasattr(article, 'city'):
            schema["about"] = {
                "@type": "Place",
                "name": article.city.name,
                "description": article.city.description
            }
        
        return schema
    
    def _generate_package_schema(self, package) -> Dict[str, Any]:
        """
        Generate Product/Service schema for travel packages
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": package.name,
            "description": package.description,
            "category": "Travel Package",
            "brand": {
                "@type": "Organization",
                "name": "Travel Platform"
            }
        }
        
        if hasattr(package, 'city'):
            schema["location"] = {
                "@type": "Place",
                "name": package.city.name,
                "description": package.city.description
            }
        
        # Add offers if pricing information is available
        if hasattr(package, 'base_price'):
            schema["offers"] = {
                "@type": "Offer",
                "price": str(package.base_price),
                "priceCurrency": "INR",
                "availability": "https://schema.org/InStock"
            }
        
        return schema
    
    def _generate_city_schema(self, city) -> Dict[str, Any]:
        """
        Generate TouristDestination schema for cities
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "TouristDestination",
            "name": city.name,
            "description": city.description,
            "url": f"/cities/{city.slug}/" if hasattr(city, 'slug') else f"/cities/{city.id}/"
        }
        
        if hasattr(city, 'hero_image') and city.hero_image:
            schema["image"] = city.hero_image.url
        
        # Add tourist attractions if available
        if hasattr(city, 'highlights'):
            attractions = []
            for highlight in city.highlights.all()[:5]:  # Limit to 5
                attractions.append({
                    "@type": "TouristAttraction",
                    "name": highlight.title,
                    "description": highlight.description
                })
            if attractions:
                schema["touristAttraction"] = attractions
        
        return schema
    
    def _generate_generic_schema(self, obj) -> Dict[str, Any]:
        """
        Generate generic schema for unknown object types
        """
        return {
            "@context": "https://schema.org",
            "@type": "Thing",
            "name": getattr(obj, 'name', getattr(obj, 'title', str(obj))),
            "description": getattr(obj, 'description', ''),
            "url": f"/{obj._meta.model_name}s/{obj.id}/"
        }

class SEOUtils:
    """
    General SEO utility functions
    """
    
    @staticmethod
    def generate_meta_tags(seo_data: SEOData, canonical_url: str = '') -> str:
        """
        Generate HTML meta tags from SEO data
        """
        tags = []
        
        # Basic meta tags
        if seo_data.title:
            tags.append(f'<title>{seo_data.title}</title>')
            tags.append(f'<meta name="title" content="{seo_data.title}">')
        
        if seo_data.description:
            tags.append(f'<meta name="description" content="{seo_data.description}">')
        
        if seo_data.keywords:
            tags.append(f'<meta name="keywords" content="{seo_data.keywords}">')
        
        # Open Graph tags
        og_title = seo_data.og_title or seo_data.title
        if og_title:
            tags.append(f'<meta property="og:title" content="{og_title}">')
        
        og_description = seo_data.og_description or seo_data.description
        if og_description:
            tags.append(f'<meta property="og:description" content="{og_description}">')
        
        if seo_data.og_image:
            tags.append(f'<meta property="og:image" content="{seo_data.og_image.url}">')
        
        tags.append('<meta property="og:type" content="website">')
        
        # Canonical URL
        if canonical_url:
            tags.append(f'<link rel="canonical" href="{canonical_url}">')
        
        # Twitter Card tags
        tags.append('<meta name="twitter:card" content="summary_large_image">')
        if og_title:
            tags.append(f'<meta name="twitter:title" content="{og_title}">')
        if og_description:
            tags.append(f'<meta name="twitter:description" content="{og_description}">')
        if seo_data.og_image:
            tags.append(f'<meta name="twitter:image" content="{seo_data.og_image.url}">')
        
        return '\n'.join(tags)
    
    @staticmethod
    def generate_json_ld(structured_data: Dict[str, Any]) -> str:
        """
        Generate JSON-LD script tag from structured data
        """
        import json
        
        if not structured_data:
            return ''
        
        json_str = json.dumps(structured_data, indent=2)
        return f'<script type="application/ld+json">\n{json_str}\n</script>'
    
    @staticmethod
    def extract_keywords_from_content(content: str, max_keywords: int = 10) -> str:
        """
        Extract keywords from content (basic implementation)
        """
        import re
        from collections import Counter
        
        # Remove HTML tags and special characters
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'[^\w\s]', '', clean_content.lower())
        
        # Split into words and filter
        words = clean_content.split()
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Filter words (length > 3, not stop words)
        filtered_words = [
            word for word in words 
            if len(word) > 3 and word not in stop_words
        ]
        
        # Get most common words
        word_counts = Counter(filtered_words)
        top_words = [word for word, count in word_counts.most_common(max_keywords)]
        
        return ', '.join(top_words)
    
    @staticmethod
    def validate_seo_data(seo_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate SEO data and return errors/warnings
        """
        errors = []
        warnings = []
        
        # Title validation
        title = seo_data.get('title', '')
        if not title:
            errors.append('Title is required')
        elif len(title) < 30:
            warnings.append('Title is shorter than recommended (30-60 characters)')
        elif len(title) > 60:
            warnings.append('Title is longer than recommended (30-60 characters)')
        
        # Description validation
        description = seo_data.get('description', '')
        if not description:
            warnings.append('Meta description is recommended')
        elif len(description) < 120:
            warnings.append('Meta description is shorter than recommended (120-160 characters)')
        elif len(description) > 160:
            warnings.append('Meta description is longer than recommended (120-160 characters)')
        
        # Keywords validation
        keywords = seo_data.get('keywords', '')
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            if len(keyword_list) > 10:
                warnings.append('Too many keywords - focus on 3-10 most relevant terms')
        
        return {
            'errors': errors,
            'warnings': warnings
        }