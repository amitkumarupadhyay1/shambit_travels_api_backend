from django.urls import path
from .views import NextAuthSyncView

urlpatterns = [
    path('nextauth-sync/', NextAuthSyncView.as_view(), name='nextauth-sync'),
]
