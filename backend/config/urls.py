"""
URL configuration for SafeRoute AI backend.
Course Outcome Mapping:
- Routes to API application exposing CO1, CO2, CO3, CO4, CO5 endpoints.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('api.urls')),  # Fallback for direct /predict/, /route/, etc.
]
