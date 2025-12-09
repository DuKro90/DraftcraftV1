"""
Multi-Material Calculation Service - Phase 4C

Extends CalculationEngine to handle products with multiple materials.
Each component gets its own material-specific calculations.

Example:
    Tisch mit Nussbaum-Platte (teuer) und Eiche-Gestell (günstiger)
    → Separate Faktoren pro Komponente
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

from django.contrib.auth.models import User

from documents.schemas.multi_material_schema import (
    MultiMaterialExtraction,
    is_multi_material_extraction,
    convert_legacy_to_multi_material,
    ComponentSpecification,
)
from documents.betriebskennzahl_models import (
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    MateriallistePosition,
)

logger = logging.getLogger(__name__)


class MultiMaterialCalculationService:
    """
    Service for calculating costs of multi-material products.

    Applies TIER 1 factors (Holzart, Oberfläche, Komplexität) per component.
    """

    def __init__(self, user: User):
        """
        Initialize service for a user.

        Args:
            user: Django User instance
        """
        self.user = user
        logger.debug(f"MultiMaterialCalculationService initialized for user {user.id}")

    def calculate_multi_material_cost(
        self,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate material costs for multi-material product.

        Args:
            extracted_data: ExtractionResult.extracted_data with multi_material format

        Returns:
            {
                'components': [
                    {
                        'component_typ': 'Tischplatte',
                        'material_info': {...},
                        'base_cost': 240.00,
                        'holzart_faktor': 1.5,  # Nussbaum
                        'oberfläche_faktor': 1.10,
                        'komplexität_faktor': 1.0,
                        'total_material_cost': 396.00
                    },
                    ...
                ],
                'total_material_cost': 600.00,
                'component_count': 2
            }

        Raises:
            ValueError: If data format is invalid
        """
        # Validate multi-material format
        if not is_multi_material_extraction(extracted_data):
            raise ValueError(
                "Data is not in multi_material format. "
                "Use convert_legacy_to_multi_material() first."
            )

        # Load multi-material extraction
        extraction = MultiMaterialExtraction.from_dict(extracted_data)

        # Validate
        validation = extraction.validate()
        if not validation['valid']:
            logger.warning(
                f"Multi-material extraction has errors: {validation['errors']}"
            )
            # Continue with warnings, but log them
            for warning in validation['warnings']:
                logger.warning(f"Validation warning: {warning}")

        # Calculate each component
        component_results = []
        total_cost = Decimal('0')

        for component in extraction.components:
            component_cost = self._calculate_component_cost(component)
            component_results.append(component_cost)
            total_cost += component_cost['total_material_cost']

        return {
            'components': component_results,
            'total_material_cost': total_cost,
            'component_count': len(component_results),
            'unique_materials': len(extraction.get_unique_materials())
        }

    def _calculate_component_cost(
        self,
        component: ComponentSpecification
    ) -> Dict[str, Any]:
        """
        Calculate cost for a single component.

        Args:
            component: ComponentSpecification

        Returns:
            Component cost breakdown dict
        """
        # Step 1: Get base material cost
        base_cost = self._get_base_material_cost(component)

        # Step 2: Get material-specific factors
        holzart_faktor = self._get_holzart_faktor(component.material.holzart)
        oberfläche_faktor = self._get_oberfläche_faktor(component.material.oberfläche)
        komplexität_faktor = self._get_komplexität_faktor(component.komplexität)

        # Step 3: Calculate total
        total = base_cost * holzart_faktor * oberfläche_faktor * komplexität_faktor

        logger.debug(
            f"Component '{component.component_typ}': "
            f"Base {base_cost} × Holzart {holzart_faktor} × "
            f"Oberfläche {oberfläche_faktor} × Komplexität {komplexität_faktor} = {total}"
        )

        return {
            'component_typ': component.component_typ,
            'material_info': component.material.to_dict(),
            'maße': component.maße,
            'anzahl': component.anzahl,
            'base_cost': float(base_cost),
            'holzart_faktor': float(holzart_faktor),
            'oberfläche_faktor': float(oberfläche_faktor),
            'komplexität_faktor': float(komplexität_faktor),
            'total_material_cost': float(total)
        }

    def _get_base_material_cost(
        self,
        component: ComponentSpecification
    ) -> Decimal:
        """
        Get base material cost for component.

        Calculation:
        1. Try to find exact material in MateriallistePosition
        2. Fall back to m² pricing based on dimensions
        3. Fall back to default pricing

        Args:
            component: ComponentSpecification

        Returns:
            Base cost in EUR
        """
        # Try to find material in catalog
        material_key = f"{component.material.holzart} {component.material.stärke_mm}mm" if component.material.holzart else component.material.material_typ

        try:
            material_position = MateriallistePosition.objects.filter(
                user=self.user,
                material_bezeichnung__icontains=material_key,
                is_active=True
            ).first()

            if material_position:
                # Calculate quantity based on dimensions and unit
                quantity = self._calculate_material_quantity(
                    component.maße,
                    component.anzahl,
                    material_position.einheit
                )

                base_cost = material_position.preis_pro_einheit * Decimal(str(quantity))
                logger.debug(
                    f"Found material '{material_position.material_bezeichnung}': "
                    f"{quantity} {material_position.einheit} × {material_position.preis_pro_einheit}€ = {base_cost}€"
                )
                return base_cost

        except Exception as e:
            logger.warning(f"Error looking up material position: {e}")

        # Fallback: Calculate based on dimensions (assume m² pricing)
        area_m2 = self._calculate_area_m2(component.maße) * component.anzahl

        # Default price per m² based on material type
        default_prices = {
            'Holz': Decimal('80.00'),
            'Multiplex': Decimal('50.00'),
            'MDF': Decimal('30.00'),
            'Spanplatte': Decimal('25.00')
        }

        price_per_m2 = default_prices.get(
            component.material.material_typ,
            Decimal('60.00')  # Generic fallback
        )

        base_cost = area_m2 * price_per_m2

        logger.debug(
            f"Using fallback pricing: {area_m2:.2f} m² × {price_per_m2}€/m² = {base_cost}€"
        )

        return base_cost

    def _calculate_material_quantity(
        self,
        maße: Dict[str, float],
        anzahl: int,
        einheit: str
    ) -> Decimal:
        """
        Calculate material quantity based on dimensions and unit.

        Args:
            maße: Dimensions dict
            anzahl: Quantity of components
            einheit: Material unit (m², lfm, m³, stk)

        Returns:
            Quantity in specified unit
        """
        if einheit == 'm²' or einheit == 'm2':
            return self._calculate_area_m2(maße) * anzahl

        elif einheit == 'lfm' or einheit == 'laufmeter':
            # Use longest dimension
            länge = max(maße.get('länge', 0), maße.get('breite', 0))
            return Decimal(str(länge)) * anzahl

        elif einheit == 'm³' or einheit == 'm3':
            return self._calculate_volume_m3(maße) * anzahl

        elif einheit == 'stk' or einheit == 'stück':
            return Decimal(str(anzahl))

        else:
            logger.warning(f"Unknown unit '{einheit}', defaulting to piece count")
            return Decimal(str(anzahl))

    def _calculate_area_m2(self, maße: Dict[str, float]) -> Decimal:
        """Calculate area in m² from dimensions."""
        länge = Decimal(str(maße.get('länge', 0)))
        breite = Decimal(str(maße.get('breite', 0)))

        if länge > 0 and breite > 0:
            return länge * breite

        # Fallback: estimate 1 m²
        logger.warning(f"Insufficient dimensions for area calculation: {maße}, using 1 m²")
        return Decimal('1.0')

    def _calculate_volume_m3(self, maße: Dict[str, float]) -> Decimal:
        """Calculate volume in m³ from dimensions."""
        länge = Decimal(str(maße.get('länge', 0)))
        breite = Decimal(str(maße.get('breite', 0)))
        höhe = Decimal(str(maße.get('höhe', 0)))

        if länge > 0 and breite > 0 and höhe > 0:
            return länge * breite * höhe

        logger.warning(f"Insufficient dimensions for volume calculation: {maße}, using 0.1 m³")
        return Decimal('0.1')

    def _get_holzart_faktor(self, holzart: Optional[str]) -> Decimal:
        """
        Get wood type factor from TIER 1.

        Args:
            holzart: Wood type (e.g., 'Eiche', 'Nussbaum')

        Returns:
            Multiplier (default 1.0 if not found)
        """
        if not holzart:
            return Decimal('1.0')

        try:
            kennzahl = HolzartKennzahl.objects.get(
                holzart=holzart.lower(),
                is_active=True
            )
            return kennzahl.multiplikator
        except HolzartKennzahl.DoesNotExist:
            logger.warning(
                f"Holzart '{holzart}' not found in TIER 1, using factor 1.0"
            )
            return Decimal('1.0')

    def _get_oberfläche_faktor(self, oberfläche: Optional[str]) -> Decimal:
        """
        Get surface finish factor from TIER 1.

        Args:
            oberfläche: Surface finish (e.g., 'geölt', 'lackiert')

        Returns:
            Multiplier (default 1.0 if not found)
        """
        if not oberfläche:
            return Decimal('1.0')

        try:
            kennzahl = OberflächenbearbeitungKennzahl.objects.get(
                bearbeitung=oberfläche.lower(),
                is_active=True
            )
            return kennzahl.multiplikator
        except OberflächenbearbeitungKennzahl.DoesNotExist:
            logger.warning(
                f"Oberfläche '{oberfläche}' not found in TIER 1, using factor 1.0"
            )
            return Decimal('1.0')

    def _get_komplexität_faktor(self, komplexität: Optional[str]) -> Decimal:
        """
        Get complexity factor from TIER 1.

        Args:
            komplexität: Complexity level (e.g., 'gefräst', 'geschnitzt')

        Returns:
            Multiplier (default 1.0 if not found)
        """
        if not komplexität:
            return Decimal('1.0')

        try:
            kennzahl = KomplexitaetKennzahl.objects.get(
                komplexitaet=komplexität.lower(),
                is_active=True
            )
            return kennzahl.multiplikator
        except KomplexitaetKennzahl.DoesNotExist:
            logger.warning(
                f"Komplexität '{komplexität}' not found in TIER 1, using factor 1.0"
            )
            return Decimal('1.0')


def calculate_multi_material_cost(
    user: User,
    extracted_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function to calculate multi-material costs.

    Args:
        user: Django User instance
        extracted_data: ExtractionResult.extracted_data

    Returns:
        Multi-material cost breakdown

    Example:
        >>> extracted_data = {
        ...     'extraction_type': 'multi_material',
        ...     'product_name': 'Esstisch',
        ...     'components': [
        ...         {
        ...             'component_typ': 'Tischplatte',
        ...             'material': {'material_typ': 'Holz', 'holzart': 'Nussbaum', ...},
        ...             'maße': {'länge': 2.0, 'breite': 1.0, 'höhe': 0.04},
        ...             'anzahl': 1
        ...         },
        ...         ...
        ...     ]
        ... }
        >>> result = calculate_multi_material_cost(user, extracted_data)
        >>> print(result['total_material_cost'])
    """
    service = MultiMaterialCalculationService(user)
    return service.calculate_multi_material_cost(extracted_data)
