"""
SafeRoute AI API URL Routing
Course Outcome Mapping:
    - CO1 (Intelligent Agent Models): /api/health/, /api/meta/
    - CO2 (Informed & Uninformed Search): /api/route/
    - CO3 (Knowledge Representation): /api/rules/
    - CO4 (Probabilistic Reasoning) & CO5 (Machine Learning): /api/predict/
"""

from django.urls import path
from .views import (
    HealthCheckView,
    MetaView,
    ScenariosView,
    PredictView,
    RouteView,
    RulesView
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='api-health'),
    path('meta/', MetaView.as_view(), name='api-meta'),
    path('scenarios/', ScenariosView.as_view(), name='api-scenarios'),
    path('predict/', PredictView.as_view(), name='api-predict'),
    path('route/', RouteView.as_view(), name='api-route'),
    path('rules/', RulesView.as_view(), name='api-rules'),
]
