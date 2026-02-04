from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import SEOData
from .serializers import (
    SEODataSerializer, 
    SEODataListSerializer,
    SEODataCreateSerializer,
    SEODataUpdateSerializer,
    ContentTypeSEOSerializer,
    SEOMetaTagsSerializer,
    StructuredDataSerializer,
    SEOAnalysisSerializer,
    BulkSEOSerializer
)
from .services.seo_service import SEOService
from .utils import SEOAnalyzer, StructuredDataGenerator

class SEODataViewSet(viewsets.ModelViewSet):
    """
    Production-level SEO data viewset with comprehensive features:
    - CRUD operations for SEO data
    - Content type filtering
    - SEO analysis and recommendations
    - Bulk operations
    - Meta tags generation
    - Structured data management
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """
        Optimized queryset with filtering capabilities
        """
        queryset = SEOData.objects.select_related('content_type').all()
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            try:
                app_label, model = content_type.split('.')
                ct = ContentType.objects.get(app_label=app_label, model=model)
                queryset = queryset.filter(content_type=ct)
            except (ValueError, ContentType.DoesNotExist):
                pass
        
        # Filter by object ID
        object_id = self.request.query_params.get('object_id')
        if object_id:
            try:
                queryset = queryset.filter(object_id=int(object_id))
            except ValueError:
                pass
        
        # Search in title, description, keywords
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        return queryset.order_by('-id')
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'list':
            return SEODataListSerializer
        elif self.action == 'create':
            return SEODataCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SEODataUpdateSerializer
        return SEODataSerializer
    
    @action(detail=False, methods=['get'])
    def by_content_type(self, request):
        """
        Get SEO data grouped by content type
        """
        content_types = ContentType.objects.filter(
            seodata__isnull=False
        ).distinct().prefetch_related('seodata_set')
        
        serializer = ContentTypeSEOSerializer(content_types, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def for_object(self, request):
        """
        Get SEO data for a specific object
        """
        content_type = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')
        
        if not content_type or not object_id:
            return Response(
                {'error': 'content_type and object_id parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            app_label, model = content_type.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model)
            seo_data = SEOData.objects.get(content_type=ct, object_id=object_id)
            
            serializer = SEODataSerializer(seo_data)
            return Response(serializer.data)
        except (ValueError, ContentType.DoesNotExist):
            return Response(
                {'error': 'Invalid content_type format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except SEOData.DoesNotExist:
            return Response(
                {'error': 'SEO data not found for this object'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def meta_tags(self, request, pk=None):
        """
        Generate HTML meta tags for SEO data
        """
        seo_data = self.get_object()
        
        # Get canonical URL from request if provided
        canonical_url = request.query_params.get('canonical_url', '')
        
        data = {
            'title': seo_data.title,
            'description': seo_data.description,
            'keywords': seo_data.keywords,
            'og_title': seo_data.og_title,
            'og_description': seo_data.og_description,
            'og_image': seo_data.og_image,
            'canonical_url': canonical_url
        }
        
        serializer = SEOMetaTagsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def structured_data(self, request, pk=None):
        """
        Generate structured data (JSON-LD) for SEO
        """
        seo_data = self.get_object()
        
        if seo_data.structured_data:
            return Response(seo_data.structured_data)
        
        # Generate structured data based on content type
        generator = StructuredDataGenerator()
        structured_data = generator.generate_for_object(seo_data.content_object)
        
        return Response(structured_data)
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """
        Analyze SEO data and provide recommendations
        """
        seo_data = self.get_object()
        analyzer = SEOAnalyzer()
        analysis = analyzer.analyze_seo_data(seo_data)
        
        serializer = SEOAnalysisSerializer(analysis)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_create(self, request):
        """
        Create SEO data for multiple objects
        """
        serializer = BulkSEOSerializer(data=request.data)
        if serializer.is_valid():
            result = SEOService.bulk_create_seo_data(
                content_type=serializer.validated_data['content_type'],
                object_ids=serializer.validated_data['object_ids'],
                seo_data=serializer.validated_data['seo_data']
            )
            return Response(result)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_update(self, request):
        """
        Update SEO data for multiple objects
        """
        serializer = BulkSEOSerializer(data=request.data)
        if serializer.is_valid():
            result = SEOService.bulk_update_seo_data(
                content_type=serializer.validated_data['content_type'],
                object_ids=serializer.validated_data['object_ids'],
                seo_data=serializer.validated_data['seo_data']
            )
            return Response(result)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get SEO statistics
        """
        stats = SEOService.get_seo_stats()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def missing_seo(self, request):
        """
        Find objects missing SEO data
        """
        content_type = request.query_params.get('content_type')
        if not content_type:
            return Response(
                {'error': 'content_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            missing_objects = SEOService.find_missing_seo_data(content_type)
            return Response(missing_objects)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def generate_from_content(self, request):
        """
        Auto-generate SEO data from content object
        """
        content_type = request.data.get('content_type')
        object_id = request.data.get('object_id')
        
        if not content_type or not object_id:
            return Response(
                {'error': 'content_type and object_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            seo_data = SEOService.generate_seo_from_content(content_type, object_id)
            serializer = SEODataSerializer(seo_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def content_types(self, request):
        """
        Get available content types for SEO
        """
        # Get content types that are commonly used for SEO
        seo_content_types = [
            'articles.article',
            'packages.package', 
            'cities.city'
        ]
        
        content_types = []
        for ct_string in seo_content_types:
            try:
                app_label, model = ct_string.split('.')
                ct = ContentType.objects.get(app_label=app_label, model=model)
                content_types.append({
                    'id': ct.id,
                    'app_label': ct.app_label,
                    'model': ct.model,
                    'name': ct.name,
                    'seo_count': SEOData.objects.filter(content_type=ct).count()
                })
            except (ValueError, ContentType.DoesNotExist):
                continue
        
        return Response(content_types)

class SEOToolsViewSet(viewsets.ViewSet):
    """
    Additional SEO tools and utilities
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['post'])
    def validate_structured_data(self, request):
        """
        Validate structured data against Schema.org
        """
        serializer = StructuredDataSerializer(data=request.data)
        if serializer.is_valid():
            # Here you could integrate with Google's Structured Data Testing Tool API
            # For now, we'll do basic validation
            return Response({
                'valid': True,
                'message': 'Structured data appears to be valid',
                'schema_type': serializer.validated_data['schema_type']
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generate_sitemap_data(self, request):
        """
        Generate sitemap data for SEO objects
        """
        content_type = request.data.get('content_type')
        if not content_type:
            return Response(
                {'error': 'content_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            sitemap_data = SEOService.generate_sitemap_data(content_type)
            return Response(sitemap_data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def seo_health_check(self, request):
        """
        Perform SEO health check across all content
        """
        health_report = SEOService.seo_health_check()
        return Response(health_report)