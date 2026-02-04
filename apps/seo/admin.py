from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
from .models import SEOData
from .services.seo_service import SEOService
from .utils import SEOAnalyzer

@admin.register(SEOData)
class SEODataAdmin(admin.ModelAdmin):
    list_display = ['title_preview', 'content_object_link', 'content_type_name', 
        'seo_score', 'has_og_data', 'has_structured_data', 'id'
    ]
    list_filter = ['content_type', 'content_type__model']
    search_fields = ['title', 'description', 'keywords']
    readonly_fields = ['content_type', 'object_id', 'seo_analysis']
    list_per_page = 50
    
    fieldsets = (
        ('Content Object', {
            'fields': ('content_type', 'object_id'),
            'description': 'The object this SEO data is attached to'
        }),
        ('Basic SEO', {
            'fields': ('title', 'description', 'keywords')
        }),
        ('Open Graph', {
            'fields': ('og_title', 'og_description', 'og_image'),
            'classes': ('collapse',)
        }),
        ('Structured Data', {
            'fields': ('structured_data',),
            'classes': ('collapse',),
            'description': 'JSON-LD structured data for search engines'
        }),
        ('Analysis', {
            'fields': ('seo_analysis',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['analyze_seo', 'generate_missing_og', 'regenerate_structured_data']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'seo-dashboard/',
                self.admin_site.admin_view(self.seo_dashboard_view),
                name='seo_dashboard'
            ),
            path(
                'bulk-generate/',
                self.admin_site.admin_view(self.bulk_generate_view),
                name='seo_bulk_generate'
            ),
        ]
        return custom_urls + urls
    
    def title_preview(self, obj):
        """Show title with length indicator"""
        title = obj.title
        length = len(title)
        
        if length == 0:
            color = 'red'
            status = 'Missing'
        elif length < 30:
            color = 'orange'
            status = 'Short'
        elif length > 60:
            color = 'orange'
            status = 'Long'
        else:
            color = 'green'
            status = 'Good'
        
        preview = title[:50] + '...' if len(title) > 50 else title
        return format_html(
            '<span style="color: {};">{}</span><br><small>({} chars - {})</small>',
            color, preview, length, status
        )
    title_preview.short_description = 'Title'
    
    def content_object_link(self, obj):
        """Show link to the content object"""
        if obj.content_object:
            try:
                url = reverse(
                    f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                    args=[obj.object_id]
                )
                return format_html(
                    '<a href="{}" target="_blank">{}</a>',
                    url, str(obj.content_object)
                )
            except:
                return str(obj.content_object)
        return 'N/A'
    content_object_link.short_description = 'Content Object'
    
    def content_type_name(self, obj):
        """Show content type in readable format"""
        return f"{obj.content_type.app_label}.{obj.content_type.model}"
    content_type_name.short_description = 'Type'
    content_type_name.admin_order_field = 'content_type'
    
    def seo_score(self, obj):
        """Show SEO score with color coding"""
        analyzer = SEOAnalyzer()
        analysis = analyzer.analyze_seo_data(obj)
        score = analysis['overall_score']
        
        colors = {
            'excellent': 'green',
            'good': 'blue',
            'fair': 'orange',
            'poor': 'red'
        }
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(score, 'black'), score.upper()
        )
    seo_score.short_description = 'SEO Score'
    
    def has_og_data(self, obj):
        """Show Open Graph completeness"""
        og_fields = [obj.og_title, obj.og_description, obj.og_image]
        completed = sum(1 for field in og_fields if field)
        
        if completed == 3:
            return format_html('<span style="color: green;">✓ Complete</span>')
        elif completed > 0:
            return format_html('<span style="color: orange;">◐ Partial</span>')
        else:
            return format_html('<span style="color: red;">✗ Missing</span>')
    has_og_data.short_description = 'Open Graph'
    
    def has_structured_data(self, obj):
        """Show structured data status"""
        if obj.structured_data:
            return format_html('<span style="color: green;">✓ Yes</span>')
        else:
            return format_html('<span style="color: red;">✗ No</span>')
    has_structured_data.short_description = 'Structured Data'
    
    def seo_analysis(self, obj):
        """Show detailed SEO analysis"""
        if not obj.pk:
            return "Save the object first to see analysis"
        
        analyzer = SEOAnalyzer()
        analysis = analyzer.analyze_seo_data(obj)
        
        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h4>SEO Analysis</h4>
            <p><strong>Overall Score:</strong> <span style="color: {'green' if analysis['overall_score'] in ['excellent', 'good'] else 'orange' if analysis['overall_score'] == 'fair' else 'red'};">{analysis['overall_score'].upper()}</span></p>
            
            <h5>Details:</h5>
            <ul>
                <li><strong>Title:</strong> {analysis['title_length']} characters ({analysis['title_score']})</li>
                <li><strong>Description:</strong> {analysis['description_length']} characters ({analysis['description_score']})</li>
                <li><strong>Keywords:</strong> {analysis['keywords_count']} keywords ({analysis['keywords_score']})</li>
                <li><strong>Open Graph:</strong> {analysis['og_completeness']*100:.0f}% complete</li>
            </ul>
            
            <h5>Recommendations:</h5>
            <ul>
        """
        
        for rec in analysis['recommendations']:
            html += f"<li>{rec}</li>"
        
        html += """
            </ul>
        </div>
        """
        
        return format_html(html)
    seo_analysis.short_description = 'SEO Analysis'
    
    def analyze_seo(self, request, queryset):
        """Analyze selected SEO entries"""
        analyzer = SEOAnalyzer()
        issues_found = 0
        
        for seo_data in queryset:
            analysis = analyzer.analyze_seo_data(seo_data)
            if analysis['overall_score'] in ['poor', 'fair']:
                issues_found += 1
        
        self.message_user(
            request,
            f'Analyzed {queryset.count()} SEO entries. Found {issues_found} with issues.',
            messages.INFO
        )
    analyze_seo.short_description = 'Analyze SEO quality'
    
    def generate_missing_og(self, request, queryset):
        """Generate missing Open Graph data"""
        updated = 0
        
        for seo_data in queryset:
            if not seo_data.og_title:
                seo_data.og_title = seo_data.title
                updated += 1
            if not seo_data.og_description:
                seo_data.og_description = seo_data.description
                updated += 1
            seo_data.save()
        
        self.message_user(
            request,
            f'Generated missing Open Graph data for {updated} fields.',
            messages.SUCCESS
        )
    generate_missing_og.short_description = 'Generate missing Open Graph data'
    
    def regenerate_structured_data(self, request, queryset):
        """Regenerate structured data"""
        from .utils import StructuredDataGenerator
        
        generator = StructuredDataGenerator()
        updated = 0
        
        for seo_data in queryset:
            if seo_data.content_object:
                structured_data = generator.generate_for_object(seo_data.content_object)
                seo_data.structured_data = structured_data
                seo_data.save()
                updated += 1
        
        self.message_user(
            request,
            f'Regenerated structured data for {updated} entries.',
            messages.SUCCESS
        )
    regenerate_structured_data.short_description = 'Regenerate structured data'
    
    def seo_dashboard_view(self, request):
        """SEO dashboard view"""
        stats = SEOService.get_seo_stats()
        health_report = SEOService.seo_health_check()
        
        # Get missing SEO data for each content type
        missing_data = {}
        for ct_data in stats['by_content_type']:
            content_type = f"{ct_data['content_type__app_label']}.{ct_data['content_type__model']}"
            try:
                missing_info = SEOService.find_missing_seo_data(content_type)
                missing_data[content_type] = missing_info
            except:
                pass
        
        context = {
            'title': 'SEO Dashboard',
            'stats': stats,
            'health_report': health_report,
            'missing_data': missing_data,
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/seo/dashboard.html', context)
    
    def bulk_generate_view(self, request):
        """Bulk generate SEO data"""
        if request.method == 'POST':
            content_type = request.POST.get('content_type')
            
            if content_type:
                try:
                    missing_info = SEOService.find_missing_seo_data(content_type)
                    object_ids = [obj['id'] for obj in missing_info['missing_objects']]
                    
                    if object_ids:
                        # Generate SEO data for missing objects
                        created_count = 0
                        for obj_id in object_ids:
                            try:
                                SEOService.generate_seo_from_content(content_type, obj_id)
                                created_count += 1
                            except Exception as e:
                                continue
                        
                        self.message_user(
                            request,
                            f'Generated SEO data for {created_count} objects.',
                            messages.SUCCESS
                        )
                    else:
                        self.message_user(
                            request,
                            'No objects missing SEO data found.',
                            messages.INFO
                        )
                        
                except Exception as e:
                    self.message_user(
                        request,
                        f'Error: {str(e)}',
                        messages.ERROR
                    )
                
                return redirect('admin:seo_seodata_changelist')
        
        # Get available content types
        content_types = []
        for ct_data in SEOService.get_seo_stats()['by_content_type']:
            content_type = f"{ct_data['content_type__app_label']}.{ct_data['content_type__model']}"
            try:
                missing_info = SEOService.find_missing_seo_data(content_type)
                if missing_info['missing_seo'] > 0:
                    content_types.append({
                        'name': content_type,
                        'missing_count': missing_info['missing_seo']
                    })
            except:
                pass
        
        context = {
            'title': 'Bulk Generate SEO Data',
            'content_types': content_types,
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/seo/bulk_generate.html', context)