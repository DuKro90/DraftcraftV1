"""
Multi-Material Data Schema - Phase 4C

Defines the structure for multi-material product extraction.
Allows different materials for different components of a product.

Example Use Cases:
- Tisch mit Nussbaum-Platte und Eiche-Gestell
- Schrank mit Kiefer-Korpus und Eiche-Fronten
- Küche mit Multiplex-Korpus und Nussbaum-Sichtflächen
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass, asdict
import json


@dataclass
class MaterialSpecification:
    """
    Material specification for a single component.

    Example:
        MaterialSpecification(
            material_typ='Holz',
            holzart='Eiche',
            stärke_mm=40,
            qualität='A-Qualität',
            oberfläche='geölt'
        )
    """
    material_typ: str  # 'Holz', 'Multiplex', 'MDF', 'Metall', 'Glas', etc.
    holzart: Optional[str] = None  # 'Eiche', 'Buche', 'Nussbaum', etc.
    stärke_mm: Optional[float] = None
    qualität: Optional[str] = None  # 'A-Qualität', 'B-Qualität', etc.
    oberfläche: Optional[str] = None  # 'naturbelassen', 'geölt', 'lackiert', etc.
    farbe: Optional[str] = None
    lieferant: Optional[str] = None
    artikel_nr: Optional[str] = None
    zusatz_eigenschaften: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ComponentSpecification:
    """
    Specification for a single component with material and dimensions.

    Example:
        ComponentSpecification(
            component_typ='Tischplatte',
            material=MaterialSpecification(...),
            maße={'länge': 2.0, 'breite': 1.0, 'höhe': 0.04},
            anzahl=1
        )
    """
    component_typ: str  # 'Tischplatte', 'Gestell', 'Tür', 'Korpus', etc.
    material: MaterialSpecification
    maße: Dict[str, float]  # {'länge': 2.0, 'breite': 1.0, 'höhe': 0.04}
    anzahl: int = 1
    komplexität: Optional[str] = None  # 'gefräst', 'gedrechselt', 'geschnitzt'
    notizen: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'component_typ': self.component_typ,
            'material': self.material.to_dict(),
            'maße': self.maße,
            'anzahl': self.anzahl
        }
        if self.komplexität:
            result['komplexität'] = self.komplexität
        if self.notizen:
            result['notizen'] = self.notizen
        return result


class MultiMaterialExtraction:
    """
    Container for multi-material extraction data.

    Provides validation and helper methods for multi-material products.
    """

    SUPPORTED_MATERIAL_TYPES = [
        'Holz',
        'Multiplex',
        'MDF',
        'HDF',
        'Spanplatte',
        'OSB',
        'Metall',
        'Aluminium',
        'Edelstahl',
        'Glas',
        'Acryl',
        'Kunststoff',
        'Sonstiges'
    ]

    SUPPORTED_HOLZARTEN = [
        'Eiche',
        'Buche',
        'Nussbaum',
        'Ahorn',
        'Kirschbaum',
        'Fichte',
        'Kiefer',
        'Tanne',
        'Lärche',
        'Birke',
        'Esche',
        'Erle',
        'Mahagoni',
        'Teak',
        'Palisander',
        'Sonstiges'
    ]

    def __init__(self):
        """Initialize multi-material extraction."""
        self.components: List[ComponentSpecification] = []
        self.product_name: Optional[str] = None
        self.product_typ: Optional[str] = None  # 'Tisch', 'Schrank', 'Küche', etc.

    def add_component(
        self,
        component_typ: str,
        material_spec: MaterialSpecification,
        maße: Dict[str, float],
        anzahl: int = 1,
        komplexität: Optional[str] = None
    ) -> ComponentSpecification:
        """
        Add a component to the extraction.

        Args:
            component_typ: Type of component (e.g., 'Tischplatte', 'Gestell')
            material_spec: Material specification
            maße: Dimensions dict
            anzahl: Quantity
            komplexität: Complexity level

        Returns:
            Created ComponentSpecification
        """
        component = ComponentSpecification(
            component_typ=component_typ,
            material=material_spec,
            maße=maße,
            anzahl=anzahl,
            komplexität=komplexität
        )
        self.components.append(component)
        return component

    def get_component(self, component_typ: str) -> Optional[ComponentSpecification]:
        """Get component by type."""
        for comp in self.components:
            if comp.component_typ == component_typ:
                return comp
        return None

    def get_components_by_material(self, material_typ: str) -> List[ComponentSpecification]:
        """Get all components with specific material type."""
        return [c for c in self.components if c.material.material_typ == material_typ]

    def get_unique_materials(self) -> List[MaterialSpecification]:
        """Get list of unique materials used."""
        seen = set()
        unique = []
        for comp in self.components:
            key = (comp.material.material_typ, comp.material.holzart)
            if key not in seen:
                seen.add(key)
                unique.append(comp.material)
        return unique

    def to_dict(self) -> Dict[str, Any]:
        """
        Export to dictionary format for ExtractionResult.extracted_data.

        Returns:
            {
                'extraction_type': 'multi_material',
                'product_name': 'Esstisch',
                'product_typ': 'Tisch',
                'components': [
                    {
                        'component_typ': 'Tischplatte',
                        'material': {...},
                        'maße': {...},
                        'anzahl': 1
                    },
                    ...
                ]
            }
        """
        return {
            'extraction_type': 'multi_material',
            'product_name': self.product_name,
            'product_typ': self.product_typ,
            'components': [c.to_dict() for c in self.components]
        }

    def to_json(self) -> str:
        """Export to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiMaterialExtraction':
        """
        Create MultiMaterialExtraction from dictionary.

        Args:
            data: Dictionary from ExtractionResult.extracted_data

        Returns:
            MultiMaterialExtraction instance
        """
        extraction = cls()
        extraction.product_name = data.get('product_name')
        extraction.product_typ = data.get('product_typ')

        for comp_data in data.get('components', []):
            material_data = comp_data['material']
            material = MaterialSpecification(
                material_typ=material_data['material_typ'],
                holzart=material_data.get('holzart'),
                stärke_mm=material_data.get('stärke_mm'),
                qualität=material_data.get('qualität'),
                oberfläche=material_data.get('oberfläche'),
                farbe=material_data.get('farbe'),
                lieferant=material_data.get('lieferant'),
                artikel_nr=material_data.get('artikel_nr'),
                zusatz_eigenschaften=material_data.get('zusatz_eigenschaften')
            )

            extraction.add_component(
                component_typ=comp_data['component_typ'],
                material_spec=material,
                maße=comp_data['maße'],
                anzahl=comp_data.get('anzahl', 1),
                komplexität=comp_data.get('komplexität')
            )

        return extraction

    def validate(self) -> Dict[str, Any]:
        """
        Validate the extraction data.

        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []

        # Check if at least one component exists
        if not self.components:
            errors.append("Keine Komponenten definiert")

        # Validate each component
        for i, comp in enumerate(self.components):
            comp_prefix = f"Komponente {i+1} ({comp.component_typ})"

            # Check material type
            if comp.material.material_typ not in self.SUPPORTED_MATERIAL_TYPES:
                warnings.append(
                    f"{comp_prefix}: Unbekannter Material-Typ '{comp.material.material_typ}'"
                )

            # Check holzart for wood materials
            if comp.material.material_typ == 'Holz' and comp.material.holzart:
                if comp.material.holzart not in self.SUPPORTED_HOLZARTEN:
                    warnings.append(
                        f"{comp_prefix}: Unbekannte Holzart '{comp.material.holzart}'"
                    )

            # Check dimensions
            if not comp.maße:
                errors.append(f"{comp_prefix}: Keine Maße angegeben")
            else:
                required_dims = ['länge', 'breite', 'höhe']
                missing = [d for d in required_dims if d not in comp.maße]
                if missing:
                    warnings.append(
                        f"{comp_prefix}: Fehlende Maße: {', '.join(missing)}"
                    )

            # Check quantity
            if comp.anzahl <= 0:
                errors.append(f"{comp_prefix}: Ungültige Anzahl ({comp.anzahl})")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_multi_material_extraction(
    product_name: str,
    product_typ: str,
    components: List[Dict[str, Any]]
) -> MultiMaterialExtraction:
    """
    Helper function to create multi-material extraction from simple dict.

    Args:
        product_name: Name of product
        product_typ: Type of product
        components: List of component dicts

    Returns:
        MultiMaterialExtraction instance

    Example:
        >>> extraction = create_multi_material_extraction(
        ...     product_name='Esstisch',
        ...     product_typ='Tisch',
        ...     components=[
        ...         {
        ...             'component_typ': 'Tischplatte',
        ...             'material_typ': 'Holz',
        ...             'holzart': 'Nussbaum',
        ...             'stärke_mm': 40,
        ...             'oberfläche': 'geölt',
        ...             'maße': {'länge': 2.0, 'breite': 1.0, 'höhe': 0.04},
        ...             'anzahl': 1
        ...         },
        ...         {
        ...             'component_typ': 'Gestell',
        ...             'material_typ': 'Holz',
        ...             'holzart': 'Eiche',
        ...             'stärke_mm': 60,
        ...             'maße': {'länge': 2.0, 'breite': 1.0, 'höhe': 0.75},
        ...             'anzahl': 1
        ...         }
        ...     ]
        ... )
    """
    extraction = MultiMaterialExtraction()
    extraction.product_name = product_name
    extraction.product_typ = product_typ

    for comp_data in components:
        material = MaterialSpecification(
            material_typ=comp_data['material_typ'],
            holzart=comp_data.get('holzart'),
            stärke_mm=comp_data.get('stärke_mm'),
            qualität=comp_data.get('qualität'),
            oberfläche=comp_data.get('oberfläche'),
            farbe=comp_data.get('farbe'),
            lieferant=comp_data.get('lieferant'),
            artikel_nr=comp_data.get('artikel_nr')
        )

        extraction.add_component(
            component_typ=comp_data['component_typ'],
            material_spec=material,
            maße=comp_data['maße'],
            anzahl=comp_data.get('anzahl', 1),
            komplexität=comp_data.get('komplexität')
        )

    return extraction


def is_multi_material_extraction(extracted_data: Dict[str, Any]) -> bool:
    """
    Check if extraction data is multi-material format.

    Args:
        extracted_data: ExtractionResult.extracted_data dict

    Returns:
        True if multi-material format
    """
    return extracted_data.get('extraction_type') == 'multi_material'


def convert_legacy_to_multi_material(
    extracted_data: Dict[str, Any]
) -> MultiMaterialExtraction:
    """
    Convert legacy single-material format to multi-material format.

    Args:
        extracted_data: Legacy extraction data with single material

    Returns:
        MultiMaterialExtraction with single component

    Example:
        >>> legacy_data = {
        ...     'holzart': 'Eiche',
        ...     'oberfläche': 'geölt',
        ...     'maße': {'länge': 2.0, 'breite': 1.0, 'höhe': 0.04}
        ... }
        >>> extraction = convert_legacy_to_multi_material(legacy_data)
        >>> print(extraction.components[0].material.holzart)
        'Eiche'
    """
    extraction = MultiMaterialExtraction()
    extraction.product_typ = extracted_data.get('product_typ', 'Unbekannt')

    # Create single material specification
    material = MaterialSpecification(
        material_typ='Holz',  # Default assumption
        holzart=extracted_data.get('holzart'),
        stärke_mm=extracted_data.get('stärke_mm'),
        oberfläche=extracted_data.get('oberfläche')
    )

    # Create single component
    extraction.add_component(
        component_typ='Haupt-Komponente',
        material_spec=material,
        maße=extracted_data.get('maße', {}),
        anzahl=1
    )

    return extraction
