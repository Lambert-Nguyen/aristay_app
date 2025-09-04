from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    
    def ready(self):
        import api.signals
        # Agent's Phase 2: Register audit signals for auto-capture
        import api.audit_signals