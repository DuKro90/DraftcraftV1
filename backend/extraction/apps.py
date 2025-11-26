from django.apps import AppConfig

class ExtractionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'extraction'
    verbose_name = 'Text Extraction (OCR/NER)'
