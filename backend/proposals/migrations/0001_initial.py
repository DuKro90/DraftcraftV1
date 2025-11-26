# Generated migration for initial proposals models

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProposalTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.TextField(blank=True)),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=Decimal('75'), max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('profit_margin_percent', models.DecimalField(decimal_places=2, default=Decimal('10'), max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('overhead_factor', models.DecimalField(decimal_places=2, default=Decimal('1.10'), max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal('1.0'))])),
                ('tax_rate_percent', models.DecimalField(decimal_places=2, default=Decimal('19'), max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('currency', models.CharField(default='EUR', max_length=3)),
                ('decimal_separator', models.CharField(default=',', max_length=1)),
                ('thousand_separator', models.CharField(default='.', max_length=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-is_active', '-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Proposal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('proposal_number', models.CharField(max_length=50, unique=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('completed', 'Completed')], default='draft', max_length=20)),
                ('customer_name', models.CharField(blank=True, max_length=255)),
                ('customer_address', models.TextField(blank=True)),
                ('customer_email', models.EmailField(blank=True, max_length=254)),
                ('subtotal', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('tax_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('total', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('terms', models.TextField(blank=True)),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='proposal', to='documents.document')),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='proposals', to='proposals.proposaltemplate')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProposalLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.IntegerField(default=1)),
                ('description', models.CharField(max_length=500)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('unit', models.CharField(max_length=20)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('discount_percent', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('total', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('proposal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='proposals.proposal')),
            ],
            options={
                'ordering': ['proposal', 'position'],
                'unique_together': {('proposal', 'position')},
            },
        ),
        migrations.CreateModel(
            name='ProposalCalculationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('material_type', models.CharField(max_length=100)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('unit', models.CharField(max_length=20)),
                ('base_material_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('base_labor_hours', models.DecimalField(decimal_places=2, max_digits=10)),
                ('labor_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('complexity_factor', models.DecimalField(decimal_places=2, max_digits=4)),
                ('surface_factor', models.DecimalField(decimal_places=2, max_digits=4)),
                ('quality_tier', models.CharField(blank=True, max_length=50)),
                ('calculated_unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('proposal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calculation_logs', to='proposals.proposal')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='proposal',
            index=models.Index(fields=['document', 'status'], name='proposals_p_document_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='proposal',
            index=models.Index(fields=['proposal_number'], name='proposals_p_proposal_number_idx'),
        ),
    ]
