from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.apps import apps
from typing import Dict, List, Any, Optional
from ..models import SEOData
from ..utils import SEOAnalyzer, StructuredDataGenerator

class SEOService:
    """
    Service class for SEO business logic and operations
    """
    
    @staticmethod
    def create_seo_data(content_type: str, object_id: int, seo_data: Dict[str, Any]) -> SEOData:
        """
        Create SEO data for a specific object
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        # Check if SEO data already exists
        existing_seo = SEOData.objects.filter(content_type=ct, object_id=object_id).first()
        if existing_seo:
            raise ValueError(f"SEO data already exists for {content_type} with id {object_id}")
        
        return SEOData.objects.create(
            content_type=ct,
            object_id=object_id,
            **seo_data
        )
    
    @staticmethod
    def update_seo_data(content_type: str, object_id: int, seo_data: Dict[str, Any]) -> SEOData:
        """
        Update existing SEO data
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        seo_obj = SEOData.objects.get(content_type=ct, object_id=object_id)
        
        for key, value in seo_data.items():
            if hasattr(seo_obj, key):
                setattr(seo_obj, key, value)
        
        seo_obj.save()
        return seo_obj
    
    @staticmethod
    def get_or_create_seo_data(content_type: str, object_id: int, defaults: Dict[str, Any]) -> tuple:
        """
        Get existing SEO data or create new one
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        return SEOData.objects.get_or_create(
            content_type=ct,
            object_id=object_id,
            defaults=defaults
        )
    
    @staticmethod
    def bulk_create_seo_data(content_type: str, object_ids: List[int], seo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create SEO data for multiple objects
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        # Check which objects already have SEO data
        existing_ids = set(
            SEOData.objects.filter(
                content_type=ct, 
                object_id__in=object_ids
            ).values_list('object_id', flat=True)
        )
        
        new_ids = [obj_id for obj_id in object_ids if obj_id not in existing_ids]
        
        # Create SEO data for new objects
        seo_objects = [
            SEOData(
                content_type=ct,
                object_id=obj_id,
                **seo_data
            )
            for obj_id in new_ids
        ]
        
        created_objects = SEOData.objects.bulk_create(seo_objects)
        
        return {
            'created_count': len(created_objects),
            'skipped_count': len(existing_ids),
            'total_requested': len(object_ids),
            'created_ids': new_ids,
            'skipped_ids': list(existing_ids)
        }
    
    @staticmethod
    def bulk_update_seo_data(content_type: str, object_ids: List[int], seo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update SEO data for multiple objects
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        # Get existing SEO objects
        seo_objects = SEOData.objects.filter(
            content_type=ct,
            object_id__in=object_ids
        )
        
        updated_count = 0
        for seo_obj in seo_objects:
            for key, value in seo_data.items():
                if hasattr(seo_obj, key):
                    setattr(seo_obj, key, value)
            seo_obj.save()
            updated_count += 1
        
        return {
            'updated_count': updated_count,
            'total_requested': len(object_ids)
        }
    
    @staticmethod
    def generate_seo_from_content(content_type: str, object_id: int) -> SEOData:
        """
        Auto-generate SEO data from content object
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        # Get the actual object
        model_class = ct.model_class()
        content_object = model_class.objects.get(id=object_id)
        
        # Generate SEO data based on object type
        seo_data = SEOService._generate_seo_for_object(content_object)
        
        # Create or update SEO data
        seo_obj, created = SEOData.objects.get_or_create(
            content_type=ct,
            object_id=object_id,
            defaults=seo_data
        )
        
        if not created:
            # Update existing SEO data
            for key, value in seo_data.items():
                setattr(seo_obj, key, value)
            seo_obj.save()
        
        return seo_obj
    
    @staticmethod
    def _generate_seo_for_object(obj) -> Dict[str, Any]:
        """
        Generate SEO data based on object type and content
        """
        seo_data = {}
        
        # Common patterns for different object types
        if hasattr(obj, 'title') and hasattr(obj, 'description'):
            # Article-like objects
            seo_data['title'] = obj.title[:255]  # Truncate to field limit
            seo_data['description'] = obj.description[:500] if len(obj.description) > 500 else obj.description
            
            if hasattr(obj, 'city'):
                seo_data['keywords'] = f"{obj.title}, {obj.city.name}, travel, tourism"
            
        elif hasattr(obj, 'name') and hasattr(obj, 'description'):
            # Package/City-like objects
            seo_data['title'] = f"{obj.name} - Travel Package"
            seo_data['description'] = obj.description[:500] if len(obj.description) > 500 else obj.description
            
            if hasattr(obj, 'city'):
                seo_data['keywords'] = f"{obj.name}, {obj.city.name}, travel package, vacation"
            elif hasattr(obj, 'name'):
                seo_data['keywords'] = f"{obj.name}, travel, tourism, destination"
        
        # Generate Open Graph data
        seo_data['og_title'] = seo_data.get('title', '')
        seo_data['og_description'] = seo_data.get('description', '')
        
        # Generate structured data
        generator = StructuredDataGenerator()
        seo_data['structured_data'] = generator.generate_for_object(obj)
        
        return seo_data
    
    @staticmethod
    def get_seo_stats() -> Dict[str, Any]:
        """
        Get comprehensive SEO statistics
        """
        total_seo_data = SEOData.objects.count()
        
        # Stats by content type
        by_content_type = SEOData.objects.values(
            'content_type__app_label',
            'content_type__model'
        ).annotate(count=Count('id')).order_by('-count')
        
        # SEO completeness stats
        complete_seo = SEOData.objects.filter(
            ~Q(title='') & ~Q(description='') & ~Q(keywords='')
        ).count()
        
        with_og_data = SEOData.objects.filter(
            ~Q(og_title='') & ~Q(og_description='')
        ).count()
        
        with_structured_data = SEOData.objects.filter(
            structured_data__isnull=False
        ).count()
        
        return {
            'total_seo_data': total_seo_data,
            'by_content_type': list(by_content_type),
            'completeness': {
                'complete_basic_seo': complete_seo,
                'with_open_graph': with_og_data,
                'with_structured_data': with_structured_data,
                'basic_seo_percentage': (complete_seo / total_seo_data * 100) if total_seo_data > 0 else 0,
                'og_percentage': (with_og_data / total_seo_data * 100) if total_seo_data > 0 else 0,
                'structured_data_percentage': (with_structured_data / total_seo_data * 100) if total_seo_data > 0 else 0
            }
        }
    
    @staticmethod
    def find_missing_seo_data(content_type: str) -> Dict[str, Any]:
        """
        Find objects that are missing SEO data
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        model_class = ct.model_class()
        
        # Get all object IDs
        all_object_ids = set(model_class.objects.values_list('id', flat=True))
        
        # Get object IDs that have SEO data
        seo_object_ids = set(
            SEOData.objects.filter(content_type=ct).values_list('object_id', flat=True)
        )
        
        # Find missing IDs
        missing_ids = all_object_ids - seo_object_ids
        
        # Get details for missing objects
        missing_objects = []
        if missing_ids:
            missing_queryset = model_class.objects.filter(id__in=missing_ids)
            for obj in missing_queryset:
                missing_objects.append({
                    'id': obj.id,
                    'title': getattr(obj, 'title', getattr(obj, 'name', str(obj))),
                    'str_representation': str(obj)
                })
        
        return {
            'content_type': content_type,
            'total_objects': len(all_object_ids),
            'with_seo': len(seo_object_ids),
            'missing_seo': len(missing_ids),
            'missing_objects': missing_objects[:50]  # Limit to 50 for performance
        }
    
    @staticmethod
    def generate_sitemap_data(content_type: str) -> List[Dict[str, Any]]:
        """
        Generate sitemap data for SEO objects
        """
        app_label, model = content_type.split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)
        
        seo_objects = SEOData.objects.filter(content_type=ct).select_related('content_type')
        
        sitemap_data = []
        for seo_obj in seo_objects:
            content_obj = seo_obj.content_object
            
            # Generate URL based on object type
            url = SEOService._generate_url_for_object(content_obj)
            
            sitemap_data.append({
                'url': url,
                'title': seo_obj.title,
                'description': seo_obj.description,
                'last_modified': getattr(content_obj, 'updated_at', getattr(content_obj, 'created_at', None)),
                'priority': SEOService._get_priority_for_object(content_obj),
                'changefreq': SEOService._get_changefreq_for_object(content_obj)
            })
        
        return sitemap_data
    
    @staticmethod
    def _generate_url_for_object(obj) -> str:
        """
        Generate URL for object based on its type
        """
        if hasattr(obj, 'slug'):
            if hasattr(obj, 'city'):
                # Package or Article with city
                return f"/{obj._meta.model_name}s/{obj.slug}/"
            else:
                # City or other slug-based object
                return f"/{obj._meta.model_name}s/{obj.slug}/"
        else:
            # Fallback to ID-based URL
            return f"/{obj._meta.model_name}s/{obj.id}/"
    
    @staticmethod
    def _get_priority_for_object(obj) -> float:
        """
        Get sitemap priority based on object type
        """
        if obj._meta.model_name == 'city':
            return 0.9
        elif obj._meta.model_name == 'package':
            return 0.8
        elif obj._meta.model_name == 'article':
            return 0.7
        else:
            return 0.5
    
    @staticmethod
    def _get_changefreq_for_object(obj) -> str:
        """
        Get change frequency based on object type
        """
        if obj._meta.model_name == 'city':
            return 'monthly'
        elif obj._meta.model_name == 'package':
            return 'weekly'
        elif obj._meta.model_name == 'article':
            return 'monthly'
        else:
            return 'yearly'
    
    @staticmethod
    def seo_health_check() -> Dict[str, Any]:
        """
        Perform comprehensive SEO health check
        """
        analyzer = SEOAnalyzer()
        
        # Get all SEO data
        all_seo_data = SEOData.objects.all()
        
        health_issues = []
        good_count = 0
        warning_count = 0
        error_count = 0
        
        for seo_data in all_seo_data:
            analysis = analyzer.analyze_seo_data(seo_data)
            
            if analysis['overall_score'] == 'excellent':
                good_count += 1
            elif analysis['overall_score'] in ['good', 'fair']:
                warning_count += 1
            else:
                error_count += 1
                health_issues.append({
                    'object': str(seo_data.content_object),
                    'issues': analysis['recommendations']
                })
        
        return {
            'total_checked': len(all_seo_data),
            'good_count': good_count,
            'warning_count': warning_count,
            'error_count': error_count,
            'health_percentage': (good_count / len(all_seo_data) * 100) if all_seo_data else 0,
            'top_issues': health_issues[:10]  # Top 10 issues
        }