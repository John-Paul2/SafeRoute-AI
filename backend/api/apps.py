"""
API App Configuration
Course Outcome: Core application wiring and model pre-loading for sub-second query performance.
"""

from django.apps import AppConfig
import os
import sys


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'SafeRoute AI REST API'

    def ready(self):
        """
        Pre-loads model singletons into memory once at startup.
        Ensures subsequent REST API requests execute in < 1.5 seconds.
        """
        # Avoid pre-loading during manage.py commands like migrate or makemigrations
        is_server = any(cmd in sys.argv for cmd in ['runserver', 'test', 'gunicorn', 'uvicorn'])
        if not is_server and not os.environ.get('DJANGO_PRELOAD_MODELS'):
            return

        try:
            print("\n[SafeRoute AI] Pre-warming in-memory AI model singletons...")
            from ml.edge_risk import get_model
            from bn.infer import get_model as get_bn_model
            from routing.astar import load_cached_graph
            from rules.engine import get_engine

            get_model()
            print(" -> XGBoost model loaded.")
            get_bn_model()
            print(" -> Bayesian Network loaded.")
            load_cached_graph()
            print(" -> OpenStreetMap road graph loaded.")
            get_engine()
            print(" -> Expert rule engine initialized.")
            print("[SafeRoute AI] All models successfully cached in memory.\n")
        except Exception as e:
            print(f"[SafeRoute AI] Note: Startup model warming skipped or deferred: {e}")
