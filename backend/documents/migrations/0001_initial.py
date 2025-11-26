# Generated migration for initial documents models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(
                    upload_to='documents/%Y/%m/',
                    validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'docx', 'txt'])]
                )),
                ('original_filename', models.CharField(max_length=255)),
                ('file_size_bytes', models.IntegerField()),
                ('status', models.CharField(
                    choices=[('uploaded', 'Uploaded'), ('processing', 'Processing'), ('completed', 'Completed'), ('error', 'Error')],
                    default='uploaded',
                    max_length=20
                )),
                ('document_type', models.CharField(default='pdf', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('retention_until', models.DateTimeField(blank=True, null=True)),
                ('is_encrypted', models.BooleanField(default=False)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExtractionResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ocr_text', models.TextField(blank=True)),
                ('extracted_data', models.JSONField(default=dict)),
                ('confidence_scores', models.JSONField(default=dict)),
                ('processing_time_ms', models.IntegerField(default=0)),
                ('error_messages', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='extraction_result', to='documents.document')),
            ],
            options={
                'verbose_name_plural': 'Extraction Results',
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[('uploaded', 'Document Uploaded'), ('viewed', 'Document Viewed'), ('processed', 'Document Processed'), ('exported', 'Data Exported'), ('deleted', 'Document Deleted')],
                    max_length=50
                )),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('details', models.JSONField(default=dict)),
                ('document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='documents.document')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['user', 'created_at'], name='documents_d_user_id_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['status'], name='documents_d_status_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['document', 'timestamp'], name='documents_a_document_id_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'timestamp'], name='documents_a_user_id_timestamp_idx'),
        ),
    ]
