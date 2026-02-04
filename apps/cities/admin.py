from django.contrib import admin
from .models import City, Highlight, TravelTip

class HighlightInline(admin.TabularInline):
    model = Highlight
    extra = 1

class TravelTipInline(admin.TabularInline):
    model = TravelTip
    extra = 1

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [HighlightInline, TravelTipInline]
