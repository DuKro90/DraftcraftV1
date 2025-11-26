# Generated migration for initial extraction models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtractionConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('language', models.CharField(choices=[('de', 'German'), ('en', 'English')], default='de', max_length=2)),
                ('ocr_enabled', models.BooleanField(default=True)),
                ('ocr_confidence_threshold', models.FloatField(default=0.6)),
                ('ocr_use_cuda', models.BooleanField(default=False)),
                ('ner_enabled', models.BooleanField(default=True)),
                ('ner_model', models.CharField(default='de_core_news_lg', max_length=100)),
                ('ner_confidence_threshold', models.FloatField(default=0.7)),
                ('max_file_size_mb', models.IntegerField(default=50)),
                ('timeout_seconds', models.IntegerField(default=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='MaterialExtraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('materials', models.JSONField(default=dict)),
                ('complexity_level', models.CharField(blank=True, max_length=50)),
                ('surface_finish', models.CharField(blank=True, max_length=50)),
                ('additional_features', models.JSONField(blank=True, default=list)),
                ('dimensions', models.JSONField(default=dict)),
                ('unit', models.CharField(blank=True, max_length=20)),
                ('extraction_confidence', models.FloatField(default=0.0)),
                ('requires_manual_review', models.BooleanField(default=False)),
                ('review_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='material_extraction', to='documents.document')),
            ],
        ),
        migrations.CreateModel(
            name='ExtractedEntity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity_type', models.CharField(choices=[('MATERIAL', 'Material'), ('QUANTITY', 'Quantity'), ('UNIT', 'Unit'), ('PRICE', 'Price'), ('PERSON', 'Person'), ('ORGANIZATION', 'Organization'), ('DATE', 'Date'), ('LOCATION', 'Location'), ('OTHER', 'Other')], max_length=50)),
                ('text', models.CharField(max_length=500)),
                ('start_offset', models.IntegerField()),
                ('end_offset', models.IntegerField()),
                ('confidence_score', models.FloatField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='extracted_entities', to='documents.document')),
            ],
            options={
                'ordering': ['start_offset'],
            },
        ),
        migrations.AddIndex(
            model_name='extractedentity',
            index=models.Index(fields=['document', 'entity_type'], name='extraction_e_document_id_entity_type_idx'),
        ),
    ]
