# Core Module

Shared utilities, constants, and base configurations.

## Key Components

- **constants.py** - Manufacturing specs (woods, complexity factors, surfaces)
- **models.py** (Phase 2) - Base model classes
- **utils.py** (Phase 2) - Helper functions
- **security/** (Phase 2) - Encryption & DSGVO services
- **monitoring/** (Phase 2) - Logging & metrics

## Usage

```python
from core.constants import GERMAN_WOOD_TYPES, COMPLEXITY_FACTORS

oak = GERMAN_WOOD_TYPES['eiche']
print(oak['base_time_hours_per_sqm'])  # 0.5
```

## Tests

```bash
pytest tests/test_core_constants.py
```
