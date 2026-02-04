from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet

router = DefaultRouter()
router.register(r'', ArticleViewSet, basename='article')  # This will make /api/articles/ work directly

urlpatterns = [
    path('', include(router.urls)),
]