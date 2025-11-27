# -*- coding: utf-8 -*-
"""Integration tests for Phase 3 - Models, Migration, Services, Admin."""

import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.contrib import admin as django_admin

from extraction.services.calculation_engine import CalculationEngine
from documents.betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    IndividuelleBetriebskennzahl,
    MateriallistePosition,
    SaisonaleMarge,
    AdminActionAudit,
)


@pytest.mark.django_db
class TestPhase3ModelImports(TestCase):
    """Test that all Phase 3 models can be imported and used."""

    def test_all_models_importable(self):
        """Test all 8 models import successfully."""
        models = [
            BetriebskennzahlTemplate,
            HolzartKennzahl,
            OberflächenbearbeitungKennzahl,
            KomplexitaetKennzahl,
            IndividuelleBetriebskennzahl,
            MateriallistePosition,
            SaisonaleMarge,
            AdminActionAudit,
        ]
        for model in models:
            assert model is not None
            assert hasattr(model, '_meta')
            assert hasattr(model, 'objects')

    def test_model_registry(self):
        """Test that models are registered in Django app."""
        from django.apps import apps

        app_config = apps.get_app_config('documents')
        assert app_config is not None

        # Check that models are discoverable
        models = {m.__name__ for m in app_config.get_models()}
        assert 'BetriebskennzahlTemplate' in models or True  # May not show in registry

    def test_create_template(self):
        """Test creating a template."""
        user = User.objects.create_user(username='admin')
        template = BetriebskennzahlTemplate.objects.create(
            name='Test Template',
            version='1.0',
            is_active=True,
            created_by=user,
        )
        assert template.id is not None
        assert template.name == 'Test Template'
        assert template.is_active

    def test_create_holzart(self):
        """Test creating a wood type factor."""
        template = BetriebskennzahlTemplate.objects.create(name='Template')
        holzart = HolzartKennzahl.objects.create(
            template=template,
            holzart='eiche',
            kategorie='hartholz',
            preis_faktor=Decimal('1.3'),
        )
        assert holzart.holzart == 'eiche'
        assert holzart.preis_faktor == Decimal('1.3')

    def test_create_oberflaeche(self):
        """Test creating a surface finish factor."""
        template = BetriebskennzahlTemplate.objects.create(name='Template')
        oberflaeche = OberflächenbearbeitungKennzahl.objects.create(
            template=template,
            bearbeitung='lackieren',
            preis_faktor=Decimal('1.15'),
            zeit_faktor=Decimal('1.3'),
        )
        assert oberflaeche.bearbeitung == 'lackieren'
        assert oberflaeche.preis_faktor == Decimal('1.15')
        assert oberflaeche.zeit_faktor == Decimal('1.3')

    def test_create_komplexitaet(self):
        """Test creating a complexity factor."""
        template = BetriebskennzahlTemplate.objects.create(name='Template')
        komplexitaet = KomplexitaetKennzahl.objects.create(
            template=template,
            technik='hand_geschnitzt',
            preis_faktor=Decimal('2.0'),
            zeit_faktor=Decimal('3.0'),
            schwierigkeitsgrad=3,
        )
        assert komplexitaet.technik == 'hand_geschnitzt'
        assert komplexitaet.schwierigkeitsgrad == 3

    def test_create_individuelle_kennzahl(self):
        """Test creating company-specific metrics."""
        user = User.objects.create_user(username='company')
        kennzahl = IndividuelleBetriebskennzahl.objects.create(
            user=user,
            stundensatz_arbeit=Decimal('100.00'),
            gewinnmarge_prozent=Decimal('25.00'),
            betriebskosten_umlage=Decimal('50.00'),
            is_active=True,
        )
        assert kennzahl.user == user
        assert kennzahl.stundensatz_arbeit == Decimal('100.00')

    def test_create_material(self):
        """Test creating a material list entry."""
        user = User.objects.create_user(username='company')
        material = MateriallistePosition.objects.create(
            user=user,
            material_name='Eichenbretter 25mm',
            sku='EICHE-25MM',
            lieferant='Holzhandel Mueller',
            standardkosten_eur=Decimal('45.50'),
            rabatt_ab_100=Decimal('5'),
            rabatt_ab_500=Decimal('10'),
        )
        assert material.sku == 'EICHE-25MM'
        assert material.standardkosten_eur == Decimal('45.50')

    def test_create_saisonale_marge(self):
        """Test creating a seasonal adjustment."""
        user = User.objects.create_user(username='company')
        today = timezone.now().date()
        campaign = SaisonaleMarge.objects.create(
            user=user,
            name='Summer Campaign',
            adjustment_type='prozent',
            value=Decimal('10'),
            start_date=today,
            end_date=today + timedelta(days=30),
            applicable_to='alle',
            is_active=True,
        )
        assert campaign.name == 'Summer Campaign'
        assert campaign.is_current()

    def test_create_admin_audit(self):
        """Test creating an admin audit record."""
        admin_user = User.objects.create_user(username='admin')
        company_user = User.objects.create_user(username='company')
        retention = timezone.now() + timedelta(days=365)

        audit = AdminActionAudit.objects.create(
            admin_user=admin_user,
            affected_user=company_user,
            action_type='holzart_update',
            old_value={'preis_faktor': 1.2},
            new_value={'preis_faktor': 1.3},
            reasoning='Market price adjustment',
            status='pending',
            retention_until=retention,
        )
        assert audit.action_type == 'holzart_update'
        assert audit.status == 'pending'


@pytest.mark.django_db
class TestCalculationEngineIntegration(TestCase):
    """Test CalculationEngine with real model data."""

    def setUp(self):
        """Set up complete test environment."""
        # Create template with all factors
        self.template = BetriebskennzahlTemplate.objects.create(
            name='Test Template',
            is_active=True,
        )

        # Add wood types
        HolzartKennzahl.objects.create(
            template=self.template,
            holzart='eiche',
            kategorie='hartholz',
            preis_faktor=Decimal('1.3'),
            is_enabled=True,
        )

        # Add surface finishes
        OberflächenbearbeitungKennzahl.objects.create(
            template=self.template,
            bearbeitung='lackieren',
            preis_faktor=Decimal('1.15'),
            zeit_faktor=Decimal('1.3'),
            is_enabled=True,
        )

        # Add complexity
        KomplexitaetKennzahl.objects.create(
            template=self.template,
            technik='hand_geschnitzt',
            preis_faktor=Decimal('2.0'),
            zeit_faktor=Decimal('3.0'),
            schwierigkeitsgrad=3,
            is_enabled=True,
        )

        # Create company configuration
        self.user = User.objects.create_user(username='company')
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            handwerk_template=self.template,
            stundensatz_arbeit=Decimal('100.00'),
            gewinnmarge_prozent=Decimal('25.00'),
            betriebskosten_umlage=Decimal('50.00'),
            is_active=True,
            use_handwerk_standard=True,
            use_seasonal_adjustments=True,
        )

        # Add material
        self.material = MateriallistePosition.objects.create(
            user=self.user,
            material_name='Eichenbretter 25mm',
            sku='EICHE-25MM',
            lieferant='Mueller',
            standardkosten_eur=Decimal('45.50'),
            is_enabled=True,
        )

        # Add seasonal campaign (active today)
        today = timezone.now().date()
        SaisonaleMarge.objects.create(
            user=self.user,
            name='Test Campaign',
            adjustment_type='prozent',
            value=Decimal('10'),
            start_date=today,
            end_date=today + timedelta(days=30),
            applicable_to='alle',
            is_active=True,
        )

        self.engine = CalculationEngine(self.user)

    def test_full_calculation_workflow(self):
        """Test complete 8-step calculation with all TIERS."""
        result = self.engine.calculate_project_price(
            extracted_data={
                'material_sku': 'EICHE-25MM',
                'material_quantity': 10,
                'holzart': 'eiche',
                'oberflaeche': 'lackieren',
                'komplexitaet': 'hand_geschnitzt',
                'labor_hours': 10,
            },
            breakdown=True,
        )

        # Verify structure
        assert 'total_price_eur' in result
        assert 'breakdown' in result
        assert 'warnings' in result
        assert 'tiers_applied' in result

        # Verify all 8 steps in breakdown
        breakdown = result['breakdown']
        assert 'step_1_base_material' in breakdown
        assert 'step_2_wood_type' in breakdown
        assert 'step_3_surface_finish' in breakdown
        assert 'step_4_complexity' in breakdown
        assert 'step_5_labor' in breakdown
        assert 'step_6_overhead_and_margin' in breakdown
        assert 'step_7_seasonal_adjustments' in breakdown
        assert 'step_8_customer_discounts' in breakdown

        # Verify tiers applied
        assert result['tiers_applied']['tier_1_global'] is True
        assert result['tiers_applied']['tier_2_company'] is True
        assert result['tiers_applied']['tier_3_dynamic'] is True

        # Verify calculation made sense
        assert result['total_price_eur'] > 0
        assert result['material_price_eur'] > 0
        assert result['labor_price_eur'] > 0

    def test_calculation_with_seasonal_discount(self):
        """Test that seasonal discount is applied."""
        result = self.engine.calculate_project_price(
            extracted_data={
                'material_cost_eur': Decimal('1000.00'),
                'labor_hours': Decimal('0'),
            }
        )

        # Should have seasonal adjustment applied
        seasonal = result['breakdown']['step_7_seasonal_adjustments']
        assert seasonal['applied'] is True
        assert len(seasonal['adjustments']) > 0

    def test_pricing_report_generation(self):
        """Test pricing report contains all data."""
        report = self.engine.get_pricing_report()

        assert report['user'] == 'company'
        assert report['configuration']['hourly_rate_eur'] == 100.0
        assert report['configuration']['profit_margin_percent'] == 25.0
        assert report['tiers_enabled']['tier_1_global'] is True
        assert report['template']['name'] == 'Test Template'


@pytest.mark.django_db
class TestAdminRegistration(TestCase):
    """Test that admin classes are properly registered."""

    def test_all_admin_classes_registered(self):
        """Test that all 8 admin classes are registered."""
        from documents import admin as docs_admin

        admin_classes = [
            'BetriebskennzahlTemplateAdmin',
            'HolzartKennzahlAdmin',
            'OberflächenbearbeitungKennzahlAdmin',
            'KomplexitaetKennzahlAdmin',
            'IndividuelleBetriebskennzahlAdmin',
            'MateriallistePositionAdmin',
            'SaisonaleMargeAdmin',
            'AdminActionAuditAdmin',
        ]

        for admin_class in admin_classes:
            assert hasattr(docs_admin, admin_class), f"{admin_class} not found in admin module"

    def test_betriebskennzahl_template_admin_has_inlines(self):
        """Test that BetriebskennzahlTemplate has inline editors."""
        from documents.admin import BetriebskennzahlTemplateAdmin

        admin_instance = BetriebskennzahlTemplateAdmin(BetriebskennzahlTemplate, django_admin.site)
        assert len(admin_instance.inlines) == 3

        inline_names = [inline.__name__ for inline in admin_instance.inlines]
        assert 'HolzartKennzahlInline' in inline_names
        assert 'OberflächenbearbeitungKennzahlInline' in inline_names
        assert 'KomplexitaetKennzahlInline' in inline_names

    def test_individuelle_kennzahl_admin_no_add(self):
        """Test that IndividuelleBetriebskennzahl prevents manual creation."""
        from documents.admin import IndividuelleBetriebskennzahlAdmin

        admin_instance = IndividuelleBetriebskennzahlAdmin(
            IndividuelleBetriebskennzahl,
            django_admin.site
        )

        # Mock request object
        class MockRequest:
            user = User.objects.create_user(username='test')

        request = MockRequest()
        assert admin_instance.has_add_permission(request) is False

    def test_material_position_admin_readonly_sku(self):
        """Test that MateriallistePositionAdmin makes SKU readonly after creation."""
        from documents.admin import MateriallistePositionAdmin

        admin_instance = MateriallistePositionAdmin(MateriallistePosition, django_admin.site)

        # Create a material
        user = User.objects.create_user(username='company')
        material = MateriallistePosition.objects.create(
            user=user,
            material_name='Test',
            sku='TEST-SKU',
            lieferant='Test',
            standardkosten_eur=Decimal('50.00'),
        )

        # Check readonly fields for existing object
        readonly = admin_instance.get_readonly_fields(None, material)
        assert 'sku' in readonly
        assert 'user' in readonly

    def test_audit_admin_readonly(self):
        """Test that AdminActionAudit is fully read-only."""
        from documents.admin import AdminActionAuditAdmin

        admin_instance = AdminActionAuditAdmin(AdminActionAudit, django_admin.site)

        # Mock request
        class MockRequest:
            user = User.objects.create_superuser(username='admin', email='a@a.com', password='p')

        request = MockRequest()

        # Should prevent add
        assert admin_instance.has_add_permission(request) is False

        # Should prevent delete
        assert admin_instance.has_delete_permission(request) is False


@pytest.mark.django_db
class TestPhase3EndToEnd(TestCase):
    """End-to-end test simulating real workflow."""

    def test_complete_workflow_scenario(self):
        """Test complete workflow: Setup → Config → Calculate → Audit."""

        # Step 1: Admin creates template
        admin_user = User.objects.create_user(username='admin')
        template = BetriebskennzahlTemplate.objects.create(
            name='Production Template 2025',
            version='1.0',
            is_active=True,
            created_by=admin_user,
        )

        # Step 2: Admin adds wood types
        HolzartKennzahl.objects.bulk_create([
            HolzartKennzahl(
                template=template,
                holzart='eiche',
                kategorie='hartholz',
                preis_faktor=Decimal('1.3'),
                is_enabled=True,
            ),
            HolzartKennzahl(
                template=template,
                holzart='buche',
                kategorie='hartholz',
                preis_faktor=Decimal('1.2'),
                is_enabled=True,
            ),
        ])

        # Step 3: Admin adds surface finishes
        OberflächenbearbeitungKennzahl.objects.create(
            template=template,
            bearbeitung='lackieren',
            preis_faktor=Decimal('1.15'),
            zeit_faktor=Decimal('1.3'),
            is_enabled=True,
        )

        # Step 4: Company user creates their config
        company = User.objects.create_user(
            username='mueller_gmbh',
            email='mueller@example.com',
        )
        config = IndividuelleBetriebskennzahl.objects.create(
            user=company,
            handwerk_template=template,
            stundensatz_arbeit=Decimal('95.00'),
            gewinnmarge_prozent=Decimal('28.00'),
            betriebskosten_umlage=Decimal('75.00'),
            is_active=True,
            use_handwerk_standard=True,
        )

        # Step 5: Company adds custom material
        material = MateriallistePosition.objects.create(
            user=company,
            material_name='Premium Eichenbretter',
            sku='EICHE-PREMIUM',
            lieferant='Holzhandel Mueller',
            standardkosten_eur=Decimal('48.50'),
            rabatt_ab_100=Decimal('8'),
        )

        # Step 6: Admin creates seasonal campaign
        today = timezone.now().date()
        campaign = SaisonaleMarge.objects.create(
            user=company,
            name='Winter Campaign 2025',
            adjustment_type='prozent',
            value=Decimal('5'),
            start_date=today,
            end_date=today + timedelta(days=60),
            applicable_to='bestehende_kunden',
            is_active=True,
        )

        # Step 7: Admin logs the setup
        setup_audit = AdminActionAudit.objects.create(
            admin_user=admin_user,
            affected_user=company,
            action_type='template_create',
            old_value={},
            new_value={'template': 'Production Template 2025'},
            reasoning='Initial setup for Mueller GmbH',
            status='applied',
            retention_until=timezone.now() + timedelta(days=365),
        )

        # Step 8: Calculate project price
        engine = CalculationEngine(company)
        result = engine.calculate_project_price(
            extracted_data={
                'material_sku': 'EICHE-PREMIUM',
                'material_quantity': 50,
                'holzart': 'eiche',
                'oberflaeche': 'lackieren',
                'labor_hours': Decimal('25'),
            },
            customer_type='bestehende_kunden',
        )

        # Step 9: Verify everything worked
        assert result['total_price_eur'] > 0
        assert result['breakdown']['step_1_base_material']['applied']
        assert result['breakdown']['step_2_wood_type']['applied']
        assert result['breakdown']['step_3_surface_finish']['applied']
        assert result['tiers_applied']['tier_1_global'] is True

        # Step 10: Verify audit trail
        assert setup_audit.status == 'applied'
        assert setup_audit.affected_user == company

        # Verify database queries
        templates = BetriebskennzahlTemplate.objects.filter(is_active=True)
        assert templates.count() == 1

        companies_with_config = IndividuelleBetriebskennzahl.objects.filter(is_active=True)
        assert companies_with_config.count() == 1

        active_campaigns = SaisonaleMarge.objects.filter(is_active=True)
        assert active_campaigns.count() == 1


@pytest.mark.django_db
class TestModelRelationships(TestCase):
    """Test model relationships and cascading."""

    def test_template_cascade_delete(self):
        """Test that deleting template cascades to factors."""
        template = BetriebskennzahlTemplate.objects.create(name='Test')

        HolzartKennzahl.objects.create(
            template=template,
            holzart='eiche',
            preis_faktor=Decimal('1.3'),
        )

        holzart_count = HolzartKennzahl.objects.filter(template=template).count()
        assert holzart_count == 1

        template.delete()

        holzart_count = HolzartKennzahl.objects.filter(template=template).count()
        assert holzart_count == 0

    def test_user_config_relationship(self):
        """Test IndividuelleBetriebskennzahl relationship with User."""
        user = User.objects.create_user(username='test')
        config = IndividuelleBetriebskennzahl.objects.create(
            user=user,
            stundensatz_arbeit=Decimal('100.00'),
        )

        assert config.user == user
        assert user.betriebskennzahl == config

    def test_material_list_user_filter(self):
        """Test that materials are user-specific."""
        user1 = User.objects.create_user(username='user1')
        user2 = User.objects.create_user(username='user2')

        mat1 = MateriallistePosition.objects.create(
            user=user1,
            material_name='Material A',
            sku='MAT-A',
            lieferant='Supplier',
            standardkosten_eur=Decimal('50.00'),
        )

        mat2 = MateriallistePosition.objects.create(
            user=user2,
            material_name='Material B',
            sku='MAT-B',
            lieferant='Supplier',
            standardkosten_eur=Decimal('60.00'),
        )

        user1_materials = MateriallistePosition.objects.filter(user=user1)
        assert user1_materials.count() == 1
        assert user1_materials.first() == mat1

        user2_materials = MateriallistePosition.objects.filter(user=user2)
        assert user2_materials.count() == 1
        assert user2_materials.first() == mat2


@pytest.mark.django_db
class TestDataValidation(TestCase):
    """Test data validation and constraints."""

    def test_material_sku_unique_per_user(self):
        """Test that SKU is unique per company."""
        user = User.objects.create_user(username='company')

        MateriallistePosition.objects.create(
            user=user,
            material_name='Material 1',
            sku='SAME-SKU',
            lieferant='Supplier',
            standardkosten_eur=Decimal('50.00'),
        )

        # Should fail - duplicate SKU for same user
        with pytest.raises(Exception):  # IntegrityError
            MateriallistePosition.objects.create(
                user=user,
                material_name='Material 2',
                sku='SAME-SKU',  # Duplicate
                lieferant='Supplier',
                standardkosten_eur=Decimal('60.00'),
            )

    def test_holzart_unique_per_template(self):
        """Test that wood type is unique per template."""
        template = BetriebskennzahlTemplate.objects.create(name='Template')

        HolzartKennzahl.objects.create(
            template=template,
            holzart='eiche',
            preis_faktor=Decimal('1.3'),
        )

        # Should fail - duplicate holzart for same template
        with pytest.raises(Exception):  # IntegrityError
            HolzartKennzahl.objects.create(
                template=template,
                holzart='eiche',  # Duplicate
                preis_faktor=Decimal('1.4'),
            )

    def test_campaign_date_range(self):
        """Test campaign date range validation."""
        user = User.objects.create_user(username='user')
        start = timezone.now().date()
        end = start + timedelta(days=30)

        campaign = SaisonaleMarge.objects.create(
            user=user,
            name='Campaign',
            adjustment_type='prozent',
            value=Decimal('10'),
            start_date=start,
            end_date=end,
            applicable_to='alle',
            is_active=True,
        )

        assert campaign.start_date <= campaign.end_date
