from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet

router = DefaultRouter()
router.register(
    r"", ArticleViewSet, basename="article"
)  # This will make /api/articles/ work directly

urlpatterns = [
    path("", include(router.urls)),
]
