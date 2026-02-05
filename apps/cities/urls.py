from django.urls import path

from .views import CityContextView, CityDetailView, CityListView

urlpatterns = [
    path("", CityListView.as_view(), name="city-list"),
    path("<int:pk>/", CityDetailView.as_view(), name="city-detail"),
    path("city-context/<slug:slug>/", CityContextView.as_view(), name="city-context"),
]
