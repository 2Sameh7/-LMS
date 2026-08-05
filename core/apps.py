from django.apps import AppConfig
import signal

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'نظام إدارة التعلم'
    
    def ready(self):
        import core.signals  # Import signal handlers