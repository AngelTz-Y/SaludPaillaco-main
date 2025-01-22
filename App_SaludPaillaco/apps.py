from django.apps import AppConfig

class AppSaludpaillacoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'App_SaludPaillaco'

    def ready(self):
        # Aquí se importa el archivo signals.py
        import App_SaludPaillaco.signals  # Asegúrate de que el nombre del archivo sea correcto
