# -*- coding: utf-8 -*-
"""CalculationEngine: Price calculation service with Betriebskennzahlen integration.

Implements the 8-step pricing workflow:
1. Get base material cost (standard or custom)
2. Apply wood type factor (TIER 1)
3. Apply surface finish factor (TIER 1)
4. Apply complexity factor (TIER 1)
5. Calculate labor time + cost
6. Add overhead/margin (TIER 2)
7. Apply seasonal adjustments (TIER 3)
8. Apply customer discounts/bulk discounts (TIER 3)

All calculations use Decimal for financial precision.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from datetime import date

from django.contrib.auth.models import User
from django.utils import timezone

from documents.betriebskennzahl_models import (
    IndividuelleBetriebskennzahl,
    MateriallistePosition,
    SaisonaleMarge,
)

logger = logging.getLogger(__name__)


class CalculationError(Exception):
    """Exception for calculation engine errors."""
    pass


class CalculationEngine:
    """
    Calculates project pricing using multi-tier Betriebskennzahlen system.

    Workflow:
    - TIER 1 (Global): Wood types, surface finishes, complexity techniques
    - TIER 2 (Company): Overhead, profit margins, labor rates
    - TIER 3 (Dynamic): Seasonal adjustments, customer discounts, bulk pricing

    Example:
        >>> engine = CalculationEngine(user)
        >>> result = engine.calculate_project_price(
        ...     extracted_data={
        ...         'holzart': 'eiche',
        ...         'oberflaeche': 'lackieren',
        ...         'komplexitaet': 'hand_geschnitzt',
        ...         'material_sku': 'EICHE-25MM',
        ...         'quantity': 10,
        ...         'labor_hours': 40
        ...     },
        ...     customer_type='bestehendenr_kunden'
        ... )
        >>> print(f"Total: {result['total_price_eur']}")
    """

    def __init__(self, user: User):
        """Initialize calculation engine for a user.

        Args:
            user: Django User instance

        Raises:
            CalculationError: If user has no Betriebskennzahl configuration
        """
        if not user:
            raise CalculationError("User is required for calculation engine")

        self.user = user

        # Load user's configuration
        try:
            self.config = IndividuelleBetriebskennzahl.objects.get(user=user)
        except IndividuelleBetriebskennzahl.DoesNotExist:
            raise CalculationError(
                f"User {user.id} has no Betriebskennzahl configuration. "
                "Please configure before pricing."
            )

        if not self.config.is_active:
            raise CalculationError(f"User {user.id} betriebskennzahl is inactive")

        logger.info(f"CalculationEngine initialized for user {user.id}")

    def calculate_project_price(
        self,
        extracted_data: Dict[str, Any],
        quantity: Optional[int] = None,
        customer_type: str = 'neue_kunden',
        breakdown: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate complete project price through 8-step workflow.

        Args:
            extracted_data: Extracted document data with fields:
                - holzart: Wood type (e.g., 'eiche', 'buche')
                - oberflaeche: Surface finish (e.g., 'lackieren', 'oelen')
                - komplexitaet: Technique complexity (e.g., 'hand_geschnitzt')
                - material_sku: Optional custom material SKU
                - material_quantity: Quantity of material needed
                - labor_hours: Estimated labor hours
            quantity: Override quantity from extracted_data
            customer_type: 'neue_kunden', 'bestehende_kunden'
            breakdown: Return detailed calculation breakdown

        Returns:
            Dict with:
            - total_price_eur: Final price
            - base_price_eur: Before any adjustments
            - breakdown: Detailed calculation steps
            - warnings: Any warnings during calculation
            - tiers_applied: Which tiers were used

        Raises:
            CalculationError: If calculation fails
        """
        logger.info(
            f"Calculating project price for user {self.user.id}: "
            f"holzart={extracted_data.get('holzart')}"
        )

        try:
            breakdown_data = {}
            warnings = []
            tiers_applied = {
                'tier_1_global': self.config.use_handwerk_standard,
                'tier_2_company': True,  # Always apply
                'tier_3_dynamic': (
                    self.config.use_seasonal_adjustments or
                    self.config.use_customer_discounts or
                    self.config.use_bulk_discounts
                ),
            }

            # Step 1: Get base material cost
            base_price = self._step_1_get_base_material_cost(
                extracted_data, breakdown_data, warnings
            )

            # Step 2-4: Apply TIER 1 factors (if enabled)
            if self.config.use_handwerk_standard:
                base_price = self._step_2_apply_wood_type(
                    base_price, extracted_data, breakdown_data, warnings
                )
                base_price = self._step_3_apply_surface_finish(
                    base_price, extracted_data, breakdown_data, warnings
                )
                base_price = self._step_4_apply_complexity(
                    base_price, extracted_data, breakdown_data, warnings
                )
            else:
                logger.debug("TIER 1 (global standards) disabled")
                breakdown_data['step_2_wood_type'] = {
                    'applied': False,
                    'reason': 'use_handwerk_standard disabled'
                }
                breakdown_data['step_3_surface_finish'] = {
                    'applied': False,
                    'reason': 'use_handwerk_standard disabled'
                }
                breakdown_data['step_4_complexity'] = {
                    'applied': False,
                    'reason': 'use_handwerk_standard disabled'
                }

            # Step 5: Calculate labor cost
            labor_price = self._step_5_calculate_labor(
                extracted_data, breakdown_data, warnings
            )

            # Step 6: Add overhead and profit margin (TIER 2)
            total_with_overhead = self._step_6_add_overhead_and_margin(
                base_price + labor_price, breakdown_data, warnings
            )

            # Step 7: Apply seasonal adjustments (TIER 3)
            with_seasonal = self._step_7_apply_seasonal_adjustments(
                total_with_overhead, extracted_data, breakdown_data, warnings
            )

            # Step 8: Apply customer discounts/bulk pricing (TIER 3)
            final_price = self._step_8_apply_customer_discounts(
                with_seasonal, extracted_data, customer_type,
                breakdown_data, warnings
            )

            return {
                'total_price_eur': float(final_price),
                'base_price_eur': float(base_price),
                'material_price_eur': float(base_price),
                'labor_price_eur': float(labor_price),
                'final_price_eur': float(final_price),
                'breakdown': breakdown_data if breakdown else {},
                'warnings': warnings,
                'tiers_applied': tiers_applied,
                'currency': 'EUR',
                'calculated_at': timezone.now().isoformat(),
            }

        except CalculationError:
            raise
        except Exception as e:
            logger.error(f"Calculation failed for user {self.user.id}: {e}")
            raise CalculationError(f"Calculation failed: {e}")

    # =====================
    # 8-STEP WORKFLOW
    # =====================

    def _step_1_get_base_material_cost(
        self,
        extracted_data: Dict[str, Any],
        breakdown_data: Dict[str, Any],
        warnings: List[str],
    ) -> Decimal:
        """Step 1: Get base material cost (custom or standard)."""
        material_sku = extracted_data.get('material_sku')
        material_quantity = extracted_data.get('material_quantity', 1)

        try:
            if self.config.use_custom_materials and material_sku:
                # Use custom material price
                material = MateriallistePosition.objects.get(
                    user=self.user,
                    sku=material_sku,
                    is_enabled=True
                )
                base_cost = material.standardkosten_eur * Decimal(str(material_quantity))

                breakdown_data['step_1_base_material'] = {
                    'method': 'custom_material_list',
                    'sku': material_sku,
                    'cost_per_unit': float(material.standardkosten_eur),
                    'quantity': material_quantity,
                    'total_cost_eur': float(base_cost),
                }
                logger.debug(f"Using custom material: {material_sku}")

            else:
                # Use extracted material cost (if provided) or standard estimate
                extracted_cost = extracted_data.get('material_cost_eur', Decimal('0'))
                base_cost = Decimal(str(extracted_cost)) if extracted_cost else Decimal('100.00')

                breakdown_data['step_1_base_material'] = {
                    'method': 'extracted_or_default',
                    'cost_eur': float(base_cost),
                    'source': 'extracted_data' if extracted_cost else 'default_estimate',
                }
                logger.debug(f"Using extracted/default material cost: {base_cost}")

            return base_cost

        except MateriallistePosition.DoesNotExist:
            warning = f"Custom material not found: {material_sku}. Using default estimate."
            warnings.append(warning)
            logger.warning(warning)
            breakdown_data['step_1_base_material'] = {
                'method': 'default_estimate',
                'cost_eur': 100.0,
                'reason': f'Material SKU not found: {material_sku}'
            }
            return Decimal('100.00')

    def _step_2_apply_wood_type(
        self,
        price: Decimal,
        extracted_data: Dict[str, Any],
        breakdown_data: Dict[str, Any],
        warnings: List[str],
    ) -> Decimal:
        """Step 2: Apply wood type (Holzart) pricing factor (TIER 1)."""
        holzart = extracted_data.get('holzart', '').lower()

        if not holzart or not self.config.handwerk_template:
            breakdown_data['step_2_wood_type'] = {
                'applied': False,
                'reason': 'No holzart specified or template not configured'
            }
            return price

        try:
            from documents.betriebskennzahl_models import HolzartKennzahl

            factor = HolzartKennzahl.objects.get(
                template=self.config.handwerk_template,
                holzart=holzart,
                is_enabled=True
            )

            adjusted_price = price * factor.preis_faktor
            breakdown_data['step_2_wood_type'] = {
                'applied': True,
                'holzart': holzart,
                'factor': float(factor.preis_faktor),
                'price_before_eur': float(price),
                'price_after_eur': float(adjusted_price),
            }
            logger.debug(f"Applied holzart factor: {holzart} × {factor.preis_faktor}")
            return adjusted_price

        except Exception as e:
            warning = f"Wood type factor not found: {holzart}"
            warnings.append(warning)
            logger.debug(f"Holzart not found: {holzart}")
            breakdown_data['step_2_wood_type'] = {
                'applied': False,
                'holzart': holzart,
                'reason': 'Factor not configured'
            }
            return price

    def _step_3_apply_surface_finish(
        self,
        price: Decimal,
        extracted_data: Dict[str, Any],
        breakdown_data: Dict[str, Any],
        warnings: List[str],
    ) -> Decimal:
        """Step 3: Apply surface finish (Oberflächenbearbeitung) factor (TIER 1)."""
        oberflaeche = extracted_data.get('oberflaeche', '').lower()

        if not oberflaeche or not self.config.handwerk_template:
            breakdown_data['step_3_surface_finish'] = {
                'applied': False,
                'reason': 'No oberflaeche specified or template not configured'
            }
            return price

        try:
            from documents.betriebskennzahl_models import OberflächenbearbeitungKennzahl

            factor = OberflächenbearbeitungKennzahl.objects.get(
                template=self.config.handwerk_template,
                bearbeitung=oberflaeche,
                is_enabled=True
            )

            adjusted_price = price * factor.preis_faktor
            breakdown_data['step_3_surface_finish'] = {
                'applied': True,
                'bearbeitung': oberflaeche,
                'price_factor': float(factor.preis_faktor),
                'time_factor': float(factor.zeit_faktor),
                'price_before_eur': float(price),
                'price_after_eur': float(adjusted_price),
            }
            logger.debug(f"Applied oberflaeche factor: {oberflaeche} × {factor.preis_faktor}")
            return adjusted_price

        except Exception as e:
            warning = f"Surface finish factor not found: {oberflaeche}"
            warnings.append(warning)
            logger.debug(f"Oberflaeche not found: {oberflaeche}")
            breakdown_data['step_3_surface_finish'] = {
                'applied': False,
                'bearbeitung': oberflaeche,
                'reason': 'Factor not configured'
            }
            return price

    def _step_4_apply_complexity(
        self,
        price: Decimal,
        extracted_data: Dict[str, Any],
        breakdown_data: Dict[str, Any],
        warnings: List[str],
    ) -> Decimal:
        """Step 4: Apply complexity (Komplexität) technique factor (TIER 1)."""
        komplexitaet = extracted_data.get('komplexitaet', '').lower()

        if not komplexitaet or not self.config.handwerk_template:
            breakdown_data['step_4_complexity'] = {
                'applied': False,
                'reason': 'No komplexitaet specified or template not configured'
            }
            return price

        try:
            from documents.betriebskennzahl_models import KomplexitaetKennzahl

            factor = KomplexitaetKennzahl.objects.get(
                template=self.config.handwerk_template,
                technik=komplexitaet,
                is_enabled=True
            )

            adjusted_price = price * factor.preis_faktor
            breakdown_data['step_4_complexity'] = {
                'applied': True,
                'technik': komplexitaet,
                'difficulty': factor.get_schwierigkeitsgrad_display(),
                'price_factor': float(factor.preis_faktor),
                'time_factor': float(factor.zeit_faktor),
                'price_before_eur': float(price),
                'price_after_eur': float(adjusted_price),
            }
            logger.debug(f"Applied komplexitaet factor: {komplexitaet} × {factor.preis_faktor}")
            return adjusted_price

        except Exception as e:
            warning = f"Complexity factor not found: {komplexitaet}"
            warnings.append(warning)
            logger.debug(f"Komplexitaet not found: {komplexitaet}")
            breakdown_data['step_4_complexity'] = {
                'applied': False,
                'technik': komplexitaet,
                'reason': 'Factor not configured'
            }
            return price

    def _step_5_calculate_labor(
        self,
        extracted_data: Dict[str, Any],
        breakdown_data: Dict[str, Any],
        warnings: List[str],
    ) -> Decimal:
        """Step 5: Calculate labor cost from estimated hours."""
        labor_hours = Decimal(str(extracted_data.get('labor_hours', 0)))

        if labor_hours <= 0:
            breakdown_data['step_5_labor'] = {
                'hours': 0,
                'hourly_rate_eur': float(self.config.stundensatz_arbeit),
                'total_cost_eur': 0.0,
            }
            return Decimal('0')

        labor_cost = labor_hours * self.config.stundensatz_arbeit
        breakdown_data['step_5_labor'] = {
            'hours': float(labor_hours),
            'hourly_rate_eur': float(self.config.stundensatz_arbeit),
            'total_cost_eur': float(labor_cost),
        }
        logger.debug(f"Labor cost: {labor_hours}h × {self.config.stundensatz_arbeit}€/h = {labor_cost}€")
        return labor_cost

    def _step_6_add_overhead_and_margin(
        self,
        material_and_labor_cost: Decimal,
        breakdown_data: Dict[str, Any],
        warnings: List[str],
    ) -> Decimal:
        """Step 6: Add overhead and profit margin (TIER 2)."""
        # Add overhead allocation
        cost_with_overhead = material_and_labor_cost + self.config.betriebskosten_umlage

        # Apply profit margin
        margin_multiplier = 1 + (self.config.gewinnmarge_prozent / Decimal('100'))
        final_price = cost_with_overhead * margin_multiplier

        breakdown_data['step_6_overhead_and_margin'] = {
            'material_and_labor_cost_eur': float(material_and_labor_cost),
            'overhead_allocation_eur': float(self.config.betriebskosten_umlage),
            'cost_with_overhead_eur': float(cost_with_overhead),
            'profit_margin_percent': float(self.config.gewinnmarge_prozent),
            'margin_multiplier': float(margin_multiplier),
            'total_with_margin_eur': float(final_price),
        }
        logger.debug(
            f"Overhead: {self.config.betriebskosten_umlage}€, "
            f"Margin: {self.config.gewinnmarge_prozent}% → {final_price}€"
        )
        return final_price

    def _step_7_apply_seasonal_adjustments(
        self,
        price: Decimal,
        extracted_data: Dict[str, Any],
        breakdown_data: Dict[str, Any],
        warnings: List[str],
    ) -> Decimal:
        """Step 7: Apply seasonal/campaign adjustments (TIER 3)."""
        if not self.config.use_seasonal_adjustments:
            breakdown_data['step_7_seasonal_adjustments'] = {
                'applied': False,
                'reason': 'use_seasonal_adjustments disabled'
            }
            return price

        try:
            today = timezone.now().date()
            adjustments = SaisonaleMarge.objects.filter(
                user=self.user,
                is_active=True,
                start_date__lte=today,
                end_date__gte=today,
            )

            adjusted_price = price
            adjustment_details = []

            for adjustment in adjustments:
                if adjustment.adjustment_type == 'prozent':
                    adjustment_amount = price * (adjustment.value / Decimal('100'))
                else:  # absolute
                    adjustment_amount = adjustment.value

                adjusted_price -= adjustment_amount
                adjustment_details.append({
                    'name': adjustment.name,
                    'type': adjustment.get_adjustment_type_display(),
                    'value': float(adjustment.value),
                    'adjustment_amount_eur': float(adjustment_amount),
                })
                logger.debug(f"Applied seasonal adjustment: {adjustment.name} (-{adjustment_amount}€)")

            breakdown_data['step_7_seasonal_adjustments'] = {
                'applied': len(adjustment_details) > 0,
                'adjustments': adjustment_details,
                'price_before_eur': float(price),
                'price_after_eur': float(adjusted_price),
            }
            return adjusted_price

        except Exception as e:
            logger.error(f"Error applying seasonal adjustments: {e}")
            breakdown_data['step_7_seasonal_adjustments'] = {
                'applied': False,
                'error': str(e)
            }
            return price

    def _step_8_apply_customer_discounts(
        self,
        price: Decimal,
        extracted_data: Dict[str, Any],
        customer_type: str,
        breakdown_data: Dict[str, Any],
        warnings: List[str],
    ) -> Decimal:
        """Step 8: Apply customer discounts and bulk pricing (TIER 3)."""
        if not self.config.use_customer_discounts and not self.config.use_bulk_discounts:
            breakdown_data['step_8_customer_discounts'] = {
                'applied': False,
                'reason': 'Customer and bulk discounts disabled'
            }
            return price

        discount_details = []
        adjusted_price = price

        # Customer-specific discount
        if self.config.use_customer_discounts:
            customer_discount = self._get_customer_discount(customer_type)
            if customer_discount > 0:
                discount_amount = price * (customer_discount / Decimal('100'))
                adjusted_price -= discount_amount
                discount_details.append({
                    'type': 'customer_type_discount',
                    'customer_type': customer_type,
                    'discount_percent': float(customer_discount),
                    'discount_amount_eur': float(discount_amount),
                })
                logger.debug(f"Customer discount ({customer_type}): {customer_discount}%")

        # Bulk discount (if material with quantity)
        if self.config.use_bulk_discounts:
            bulk_discount = self._get_bulk_discount(extracted_data)
            if bulk_discount > 0:
                discount_amount = price * (bulk_discount / Decimal('100'))
                adjusted_price -= discount_amount
                discount_details.append({
                    'type': 'bulk_discount',
                    'quantity': extracted_data.get('material_quantity', 0),
                    'discount_percent': float(bulk_discount),
                    'discount_amount_eur': float(discount_amount),
                })
                logger.debug(f"Bulk discount: {bulk_discount}%")

        breakdown_data['step_8_customer_discounts'] = {
            'applied': len(discount_details) > 0,
            'discounts': discount_details,
            'price_before_eur': float(price),
            'price_after_eur': float(adjusted_price),
        }
        return adjusted_price

    # =====================
    # HELPER METHODS
    # =====================

    def _get_customer_discount(self, customer_type: str) -> Decimal:
        """Get customer-specific discount (expandable)."""
        # This is a placeholder - expand with your customer tiers
        customer_discounts = {
            'neue_kunden': Decimal('0'),          # No discount
            'bestehende_kunden': Decimal('5'),    # 5% for existing
            'vip_kunden': Decimal('10'),          # 10% for VIP
            'gross_kunden': Decimal('15'),        # 15% for bulk customers
        }
        return customer_discounts.get(customer_type, Decimal('0'))

    def _get_bulk_discount(self, extracted_data: Dict[str, Any]) -> Decimal:
        """Get bulk discount from material list or quantity."""
        material_sku = extracted_data.get('material_sku')
        material_quantity = extracted_data.get('material_quantity', 0)

        if not material_sku or material_quantity <= 0:
            return Decimal('0')

        try:
            material = MateriallistePosition.objects.get(
                user=self.user,
                sku=material_sku,
                is_enabled=True
            )
            return Decimal(str(material.get_discount_percent(material_quantity)))
        except MateriallistePosition.DoesNotExist:
            return Decimal('0')

    def get_pricing_report(self) -> Dict[str, Any]:
        """Generate a pricing configuration report for admin."""
        return {
            'user': self.user.username,
            'configuration': {
                'hourly_rate_eur': float(self.config.stundensatz_arbeit),
                'profit_margin_percent': float(self.config.gewinnmarge_prozent),
                'overhead_allocation_eur': float(self.config.betriebskosten_umlage),
            },
            'tiers_enabled': {
                'tier_1_global': self.config.use_handwerk_standard,
                'tier_2_company': True,
                'tier_3_dynamic': (
                    self.config.use_seasonal_adjustments or
                    self.config.use_customer_discounts or
                    self.config.use_bulk_discounts
                ),
            },
            'template': {
                'name': self.config.handwerk_template.name if self.config.handwerk_template else None,
                'version': self.config.handwerk_template.version if self.config.handwerk_template else None,
            },
        }
