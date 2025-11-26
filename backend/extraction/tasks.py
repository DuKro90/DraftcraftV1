"""Celery async tasks for document extraction."""
import logging
from celery import shared_task
from django.core.files.storage import default_storage
from documents.models import Document, ExtractionResult, AuditLog
from extraction.models import MaterialExtraction, ExtractionConfig
from extraction.services import GermanOCRService, GermanNERService
from extraction.services.base_service import ExtractionServiceError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_async(self, document_id: str, user_id: int = None) -> dict:
    """Async task to process document with OCR/NER.

    Args:
        document_id: Document UUID
        user_id: User ID (for audit logging)

    Returns:
        Dictionary with processing results
    """
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return {'status': 'error', 'message': 'Document not found'}

    try:
        # Update status
        document.status = 'processing'
        document.save(update_fields=['status'])

        # Get extraction config
        try:
            config = ExtractionConfig.objects.get(language='de')
            config_dict = {
                'ocr_use_cuda': config.ocr_use_cuda,
                'ocr_confidence_threshold': config.ocr_confidence_threshold,
                'ner_model': config.ner_model,
                'ner_confidence_threshold': config.ner_confidence_threshold,
                'max_file_size_mb': config.max_file_size_mb,
            }
        except ExtractionConfig.DoesNotExist:
            config_dict = {'max_file_size_mb': 50}

        # OCR processing
        logger.info(f"Starting OCR for document {document_id}")
        ocr_service = GermanOCRService(config_dict)
        ocr_result = ocr_service.process(document.file.path)
        logger.info(f"OCR completed for {document_id}: confidence={ocr_result['confidence']:.2f}")

        # NER processing
        logger.info(f"Starting NER for document {document_id}")
        ner_service = GermanNERService(config_dict)
        ner_result = ner_service.process(ocr_result['text'], document)
        logger.info(f"NER completed for {document_id}: entities={len(ner_result['entities'])}")

        # Create/update ExtractionResult
        extraction_result, created = ExtractionResult.objects.update_or_create(
            document=document,
            defaults={
                'ocr_text': ocr_result['text'],
                'confidence_scores': {
                    'ocr': ocr_result['confidence'],
                    'ner': ner_result['confidence'],
                },
                'processing_time_ms': ocr_result['processing_time_ms'] + ner_result['processing_time_ms'],
                'extracted_data': {
                    'entities': ner_result['summary'],
                    'entity_count': len(ner_result['entities']),
                }
            }
        )

        # Create MaterialExtraction if needed
        if ner_result['entities']:
            material_data = _extract_material_specs(ner_result['entities'])
            MaterialExtraction.objects.update_or_create(
                document=document,
                defaults={
                    'materials': material_data.get('materials', {}),
                    'complexity_level': material_data.get('complexity_level', ''),
                    'surface_finish': material_data.get('surface_finish', ''),
                    'extraction_confidence': ner_result['confidence'],
                    'requires_manual_review': ner_result['confidence'] < 0.8,
                }
            )

        # Update document status
        document.status = 'completed'
        document.save(update_fields=['status'])

        # Log processing
        if user_id:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=user_id)
                AuditLog.objects.create(
                    document=document,
                    user=user,
                    action='processed',
                    details={
                        'ocr_confidence': ocr_result['confidence'],
                        'ner_confidence': ner_result['confidence'],
                        'entity_count': len(ner_result['entities']),
                        'async': True,
                    }
                )
            except:
                pass

        logger.info(f"Successfully processed document {document_id}")

        return {
            'status': 'success',
            'document_id': str(document_id),
            'ocr_confidence': ocr_result['confidence'],
            'ner_confidence': ner_result['confidence'],
            'entity_count': len(ner_result['entities']),
            'processing_time_ms': extraction_result.processing_time_ms,
        }

    except ExtractionServiceError as e:
        logger.error(f"Extraction service error for {document_id}: {str(e)}")
        document.status = 'error'
        document.save(update_fields=['status'])

        # Log error
        if user_id:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=user_id)
                AuditLog.objects.create(
                    document=document,
                    user=user,
                    action='processed',
                    details={'error': str(e), 'async': True}
                )
            except:
                pass

        # Retry with exponential backoff
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s
            logger.info(f"Retrying document {document_id} in {countdown}s (attempt {retry_count + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=countdown)

        return {
            'status': 'error',
            'document_id': str(document_id),
            'message': str(e),
        }

    except Exception as e:
        logger.exception(f"Unexpected error processing document {document_id}")
        document.status = 'error'
        document.save(update_fields=['status'])
        return {
            'status': 'error',
            'document_id': str(document_id),
            'message': 'Unexpected error during processing',
        }


@shared_task
def cleanup_old_documents(days: int = 90) -> dict:
    """Task to delete expired documents per DSGVO.

    Args:
        days: Delete documents older than this many days

    Returns:
        Dictionary with cleanup results
    """
    from django.utils import timezone
    from datetime import timedelta

    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        documents = Document.objects.filter(
            retention_until__lt=cutoff_date
        )

        count = documents.count()
        logger.info(f"Deleting {count} expired documents")

        # Delete associated audit logs first
        for doc in documents:
            AuditLog.objects.create(
                document=doc,
                action='deleted',
                details={'reason': 'DSGVO retention period expired'}
            )

        documents.delete()

        return {
            'status': 'success',
            'deleted_count': count,
        }

    except Exception as e:
        logger.exception("Error cleaning up old documents")
        return {
            'status': 'error',
            'message': str(e),
        }


def _extract_material_specs(entities: list) -> dict:
    """Extract material specifications from entities.

    Args:
        entities: List of extracted entities

    Returns:
        Dictionary with material specifications
    """
    material_data = {}
    materials = {}

    for entity in entities:
        if entity['type'] == 'MATERIAL':
            materials[entity['text'].lower()] = 1.0
        elif entity['type'] == 'QUANTITY':
            material_data['quantity'] = entity['text']

    material_data['materials'] = materials
    return material_data
