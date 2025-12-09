# Selektives Agentic RAG Implementation Guide
## Gemini Flash 1.5 Integration in bestehende DraftCraft-Struktur

**Ziel:** Erweitern der vorhandenen Django-Pipeline um strategische Agent-Insertion Points ohne bestehende Features zu brechen.

**Baseline:** 92% NER-Accuracy → **Ziel:** 96-98% bei <10€/Monat LLM-Kosten

---

## 🎯 Architektur-Übersicht: Bestehend + Neu

### Bestehende Struktur (NICHT ÄNDERN)
```
✅ extraction/services/ocr_service.py - PaddleOCR bleibt unverändert
✅ extraction/services/ner_service.py - spaCy NER bleibt Basis-Engine  
✅ extraction/services/batch_processor.py - Orchestrierung erweitern
✅ documents/models.py - Modelle erweitern (keine Breaking Changes)
✅ api/v1/ - APIs erweitern
```

### Neue Komponenten (HINZUFÜGEN)
```
🆕 extraction/services/agent_service.py - Gemini Flash 1.5 Service
🆕 extraction/services/memory_service.py - Short/Long-term Memory
🆕 extraction/middleware/confidence_router.py - Entscheidungslogik
🆕 documents/models/agent_models.py - Memory Models
🆕 api/v1/agent_views.py - Agent-spezifische Endpoints
```

---

## Phase 1: Foundation (Woche 1-2)
*Erweitert bestehende Struktur ohne Breaking Changes*

### 1.1 Model-Erweiterungen (models/agent_models.py)

```python
# documents/models/agent_models.py - NEUE DATEI
from django.db import models
from .base import Document, ExtractionResult
import uuid

class DocumentMemory(models.Model):
    """Short-term Memory für aktuelle Batch-Session"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    
    # Memory-Pattern
    pattern_type = models.CharField(max_length=50, choices=[
        ('entity_variant', 'Entity Variation'),
        ('extraction_rule', 'Extraction Rule'),
        ('confidence_pattern', 'Confidence Pattern'),
        ('vendor_format', 'Vendor Format Pattern')
    ])
    
    pattern_data = models.JSONField()  # Gemini Context Data
    confidence = models.FloatField(default=0.0)
    usage_count = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'document_memory'
        indexes = [
            models.Index(fields=['user', 'pattern_type', '-last_used']),
        ]

class KnowledgeGraph(models.Model):
    """Long-term Memory für persistentes Lernen"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    
    # Entity-Relationship
    source_entity = models.CharField(max_length=255)
    target_entity = models.CharField(max_length=255)
    relationship_type = models.CharField(max_length=50, choices=[
        ('is_variant_of', 'Is Variant Of'),
        ('co_occurs_with', 'Co-occurs With'),
        ('vendor_specific', 'Vendor Specific'),
        ('gaeb_context', 'GAEB Context')
    ])
    
    confidence = models.FloatField(default=0.0)
    weight = models.FloatField(default=1.0)
    occurrences = models.IntegerField(default=1)
    
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'knowledge_graph'
        unique_together = ('user', 'source_entity', 'target_entity', 'relationship_type')

# documents/models/__init__.py - ERWEITERN
from .agent_models import DocumentMemory, KnowledgeGraph
```

### 1.2 Bestehende Modelle erweitern (MINIMAL)

```python
# documents/models.py - NUR ERGÄNZUNGEN, keine Änderungen
class ExtractionResult(models.Model):
    # ... bestehende Felder bleiben unverändert ...
    
    # NEUE FELDER HINZUFÜGEN:
    agent_enhanced = models.BooleanField(default=False)
    agent_confidence = models.FloatField(null=True, blank=True)
    requires_review = models.BooleanField(default=False)
    review_reasons = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'extraction_results'  # Bestehende Tabelle
```

### 1.3 Migration erstellen

```python
# Datei: documents/migrations/000X_add_agent_support.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('documents', '000X_previous_migration'),
    ]

    operations = [
        # Erweitert bestehende Tabelle
        migrations.AddField(
            model_name='extractionresult',
            name='agent_enhanced',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='extractionresult',
            name='agent_confidence',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='extractionresult',
            name='requires_review',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='extractionresult',
            name='review_reasons',
            field=models.JSONField(null=True, blank=True),
        ),
        
        # Neue Tabellen für Memory
        migrations.CreateModel(
            name='DocumentMemory',
            # ... Model Definition aus agent_models.py
        ),
        migrations.CreateModel(
            name='KnowledgeGraph',
            # ... Model Definition aus agent_models.py
        ),
    ]
```

---

## Phase 2: Gemini Service Implementation (Woche 3-4)

### 2.1 Gemini Flash Service (extraction/services/agent_service.py)

```python
# extraction/services/agent_service.py - NEUE DATEI
import google.generativeai as genai
from typing import Dict, List, Optional, TypedDict
import json
from django.conf import settings
from pydantic import BaseModel

class ExtractedEntity(BaseModel):
    type: str
    value: str
    confidence: float
    context: str

class EnhancedExtractionResult(BaseModel):
    entities: List[ExtractedEntity]
    confidence: float
    needs_review: bool
    review_reasons: Optional[List[str]] = None
    improved_fields: Optional[List[str]] = None

class GeminiAgentService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.cache_ttl = 3600  # 1 Stunde Context Cache
        
    def should_use_agent(self, extraction_result) -> bool:
        """Entscheidungslogik: Wann Agent einsetzen?"""
        confidence_scores = extraction_result.confidence_scores or {}
        
        # Quick-Checks für Agent-Bedarf
        low_confidence_fields = [
            field for field, conf in confidence_scores.items() 
            if conf < 0.85
        ]
        
        critical_fields_low = any(
            confidence_scores.get(field, 0) < 0.70
            for field in ['amount', 'date', 'gaeb_position', 'vendor_name']
        )
        
        return bool(low_confidence_fields) or critical_fields_low
    
    def enhance_extraction(self, 
                          extraction_result,
                          document_context: str,
                          memory_context: Dict = None) -> EnhancedExtractionResult:
        """Hauptmethode: NER-Ergebnis mit Gemini verbessern"""
        
        # Context für Gemini zusammenbauen
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_extraction_prompt(
            extraction_result, 
            document_context,
            memory_context or {}
        )
        
        try:
            # Gemini Flash 1.5 Aufruf mit Structured Output
            response = self.model.generate_content(
                contents=[
                    {"role": "system", "parts": [system_prompt]},
                    {"role": "user", "parts": [user_prompt]}
                ],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.9,
                    response_mime_type="application/json",
                    response_schema=EnhancedExtractionResult.model_json_schema()
                )
            )
            
            result_data = json.loads(response.text)
            return EnhancedExtractionResult(**result_data)
            
        except Exception as e:
            # Fallback: Ursprüngliches Ergebnis zurückgeben
            return self._fallback_result(extraction_result, str(e))
    
    def _build_system_prompt(self) -> str:
        return """Du bist ein Experte für deutsche Handwerksdokumente.

Aufgabe: Verbessere NER-Extraktionsergebnisse für deutsche Baubranche.

Spezialisierung:
- GAEB-Ordnungszahlen (Format: XX.XX.XXXX)
- Deutsche Materialien (Eiche, Buche, RG-Schaumstoff)
- Handwerksbetriebe und Zertifizierungen
- Deutsche Zahlenformate (1.250,50 €)

Vorgehen:
1. Prüfe bestehende Extraktion auf Plausibilität
2. Korrigiere nur bei klaren Fehlern
3. Markiere unsichere Felder für Review
4. Nutze Kontext aus ähnlichen Dokumenten"""

    def _build_extraction_prompt(self, 
                                extraction_result, 
                                document_context: str,
                                memory_context: Dict) -> str:
        
        # Bestehende Extraktion
        existing_data = {
            "entities": extraction_result.extracted_data.get('entities', []),
            "confidence_scores": extraction_result.confidence_scores,
            "ocr_text": extraction_result.ocr_text[:2000]  # Begrenzen für Context
        }
        
        # Memory-Context einbauen
        recent_patterns = memory_context.get('recent_patterns', [])
        known_entities = memory_context.get('known_entities', {})
        
        return f"""
Dokument-Kontext:
{document_context[:1500]}

Bestehende NER-Extraktion:
{json.dumps(existing_data, ensure_ascii=False, indent=2)}

Bekannte Muster aus Memory:
- Ähnliche Entities: {json.dumps(known_entities, ensure_ascii=False)}
- Letzte Patterns: {json.dumps(recent_patterns, ensure_ascii=False)}

Aufgaben:
1. Validiere alle Entities mit confidence < 0.85
2. Prüfe deutsche Zahlenformate (Komma als Dezimaltrenner)
3. Korrigiere GAEB-Ordnungszahlen falls falsch erkannt
4. Identifiziere übersehene kritische Felder

Antworte nur mit JSON im geforderten Schema.
Setze needs_review=true bei Unsicherheit.
"""

    def _fallback_result(self, extraction_result, error: str) -> EnhancedExtractionResult:
        """Fallback bei Gemini-Fehlern"""
        entities = [
            ExtractedEntity(
                type=e.get('type', 'UNKNOWN'),
                value=e.get('value', ''),
                confidence=e.get('confidence', 0.0),
                context=""
            )
            for e in extraction_result.extracted_data.get('entities', [])
        ]
        
        return EnhancedExtractionResult(
            entities=entities,
            confidence=0.0,
            needs_review=True,
            review_reasons=[f"Agent error: {error}"]
        )
```

### 2.2 Memory Service (extraction/services/memory_service.py)

```python
# extraction/services/memory_service.py - NEUE DATEI
from typing import Dict, List
from django.core.cache import cache
from documents.models import DocumentMemory, KnowledgeGraph
import json

class MemoryService:
    def __init__(self, user_id: int, batch_id: str = None):
        self.user_id = user_id
        self.batch_id = batch_id
        self.session_key = f"memory_session_{user_id}_{batch_id}" if batch_id else None
    
    def get_short_term_context(self, document_id: int) -> Dict:
        """Short-term Memory für aktuelle Batch-Session"""
        if not self.session_key:
            return {}
        
        # Redis Cache für Session Memory
        session_data = cache.get(self.session_key, {})
        
        # Recent patterns aus aktueller Session
        recent_patterns = session_data.get('patterns', [])
        
        # Bekannte Entities aus aktueller Session
        entity_variants = session_data.get('entity_variants', {})
        
        return {
            'recent_patterns': recent_patterns[-10:],  # Letzte 10 Patterns
            'known_entities': entity_variants,
            'session_stats': {
                'documents_processed': session_data.get('doc_count', 0),
                'avg_confidence': session_data.get('avg_confidence', 0.0)
            }
        }
    
    def get_long_term_context(self, entity_type: str = None) -> Dict:
        """Long-term Memory aus KnowledgeGraph"""
        
        queryset = KnowledgeGraph.objects.filter(user_id=self.user_id)
        
        if entity_type:
            queryset = queryset.filter(
                source_entity__icontains=entity_type
            ).order_by('-weight', '-last_seen')[:20]
        else:
            # Top-Entities basierend auf Gewichtung
            queryset = queryset.order_by('-weight', '-last_seen')[:50]
        
        # Gruppiere nach Relationship-Type
        context = {}
        for item in queryset:
            rel_type = item.relationship_type
            if rel_type not in context:
                context[rel_type] = []
            
            context[rel_type].append({
                'source': item.source_entity,
                'target': item.target_entity,
                'confidence': item.confidence,
                'occurrences': item.occurrences,
                'last_seen': item.last_seen.isoformat()
            })
        
        return context
    
    def learn_from_extraction(self, document_id: int, extraction_result, agent_result):
        """Lerne aus erfolgreicher Extraktion"""
        
        # Short-term: Session Memory aktualisieren
        if self.session_key:
            session_data = cache.get(self.session_key, {})
            
            # Patterns hinzufügen
            patterns = session_data.get('patterns', [])
            for entity in agent_result.entities:
                if entity.confidence > 0.9:  # Nur high-confidence Patterns
                    patterns.append({
                        'entity_type': entity.type,
                        'value': entity.value,
                        'context': entity.context,
                        'document_id': document_id
                    })
            
            session_data['patterns'] = patterns
            session_data['doc_count'] = session_data.get('doc_count', 0) + 1
            
            cache.set(self.session_key, session_data, timeout=3600)  # 1h TTL
        
        # Long-term: KnowledgeGraph aktualisieren
        self._update_knowledge_graph(extraction_result, agent_result)
    
    def _update_knowledge_graph(self, extraction_result, agent_result):
        """Aktualisiere persistenten KnowledgeGraph"""
        
        # Entity-Co-occurrence-Patterns
        entities = [e.value for e in agent_result.entities if e.confidence > 0.85]
        
        for i, entity_a in enumerate(entities):
            for entity_b in entities[i+1:]:
                
                # Upsert relationship
                kg_item, created = KnowledgeGraph.objects.get_or_create(
                    user_id=self.user_id,
                    source_entity=entity_a,
                    target_entity=entity_b,
                    relationship_type='co_occurs_with',
                    defaults={
                        'confidence': 0.8,
                        'weight': 1.0,
                        'occurrences': 1
                    }
                )
                
                if not created:
                    # Update existing relationship
                    kg_item.occurrences += 1
                    kg_item.weight = min(10.0, kg_item.weight + 0.1)  # Cap bei 10
                    kg_item.save()
```

### 2.3 Confidence Router (extraction/middleware/confidence_router.py)

```python
# extraction/middleware/confidence_router.py - NEUE DATEI
from typing import Dict, Tuple
from extraction.services.agent_service import GeminiAgentService
from extraction.services.memory_service import MemoryService

class ConfidenceRouter:
    """Entscheidet, welche Dokumente Agent-Verarbeitung brauchen"""
    
    def __init__(self):
        self.thresholds = {
            'auto_accept': 0.92,    # Direkt freigeben
            'agent_verify': 0.80,   # Agent prüft
            'agent_extract': 0.70,  # Agent extrahiert neu
            'human_review': 0.0     # Human Review
        }
        
        # Feldspezifische Schwellenwerte
        self.field_thresholds = {
            'amount': 0.95,
            'date': 0.95, 
            'gaeb_position': 0.95,
            'vendor_name': 0.85,
            'invoice_number': 0.85,
            'material': 0.80
        }
    
    def route_document(self, extraction_result, user_id: int, batch_id: str = None) -> Tuple[str, Dict]:
        """
        Hauptrouting-Logik
        
        Returns:
            (route, context) where route in ['auto', 'agent_verify', 'agent_extract', 'human']
        """
        
        confidence_scores = extraction_result.confidence_scores or {}
        entities = extraction_result.extracted_data.get('entities', [])
        
        # 1. Globaler Confidence-Check
        overall_confidence = self._calculate_overall_confidence(confidence_scores, entities)
        
        # 2. Kritische Felder prüfen
        critical_issues = self._check_critical_fields(confidence_scores)
        
        # 3. Complexity Scoring
        complexity_score = self._calculate_complexity_score(extraction_result)
        
        # 4. Routing-Entscheidung
        if critical_issues:
            return 'agent_extract', {'reason': 'critical_fields_low', 'issues': critical_issues}
        
        if overall_confidence >= self.thresholds['auto_accept'] and complexity_score < 0.3:
            return 'auto', {'confidence': overall_confidence}
        
        if overall_confidence >= self.thresholds['agent_verify']:
            return 'agent_verify', {'confidence': overall_confidence}
        
        if overall_confidence >= self.thresholds['agent_extract']:
            return 'agent_extract', {'confidence': overall_confidence}
        
        return 'human', {'confidence': overall_confidence, 'complexity': complexity_score}
    
    def _calculate_overall_confidence(self, confidence_scores: Dict, entities: List) -> float:
        """Gewichteter Overall-Confidence-Score"""
        if not confidence_scores:
            return 0.0
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for field, confidence in confidence_scores.items():
            weight = self._get_field_weight(field)
            weighted_sum += confidence * weight
            weight_total += weight
        
        return weighted_sum / weight_total if weight_total > 0 else 0.0
    
    def _get_field_weight(self, field: str) -> float:
        """Gewichtung nach Feldwichtigkeit"""
        weights = {
            'amount': 3.0,
            'date': 2.5,
            'gaeb_position': 2.5,
            'vendor_name': 2.0,
            'invoice_number': 2.0,
            'material': 1.5,
            'contact_person': 1.0,
            'notes': 0.5
        }
        return weights.get(field, 1.0)
    
    def _check_critical_fields(self, confidence_scores: Dict) -> List[str]:
        """Prüfe kritische Felder auf Mindest-Confidence"""
        issues = []
        
        for field, threshold in self.field_thresholds.items():
            if field in confidence_scores:
                if confidence_scores[field] < threshold:
                    issues.append(f"{field}: {confidence_scores[field]:.2f} < {threshold}")
        
        return issues
    
    def _calculate_complexity_score(self, extraction_result) -> float:
        """Document Complexity Scoring"""
        
        complexity_factors = {
            'unusual_layout': 0.0,
            'table_confidence_low': 0.0, 
            'handwriting_detected': 0.0,
            'ocr_quality_low': 0.0,
            'entity_density_unusual': 0.0,
            'new_vendor': 0.0
        }
        
        # OCR-Quality Check
        if extraction_result.confidence < 0.85:
            complexity_factors['ocr_quality_low'] = 0.3
        
        # Entity-Density Check
        entities = extraction_result.extracted_data.get('entities', [])
        word_count = len(extraction_result.ocr_text.split()) if extraction_result.ocr_text else 1
        entity_density = len(entities) / word_count
        
        if entity_density < 0.02:  # Sehr wenige Entities
            complexity_factors['entity_density_unusual'] = 0.2
        
        return min(1.0, sum(complexity_factors.values()))
```

---

## Phase 3: Integration in bestehende Pipeline (Woche 5-6)

### 3.1 BatchProcessor erweitern (MINIMAL CHANGES)

```python
# extraction/services/batch_processor.py - ERWEITERT bestehende Klasse

class BatchProcessor:
    def __init__(self, batch_id):
        self.batch_id = batch_id
        # ... bestehende Initialisierung bleibt ...
        
        # NEUE DEPENDENCIES HINZUFÜGEN
        self.agent_service = GeminiAgentService()
        self.confidence_router = ConfidenceRouter()
    
    def process_document(self, document_id: int):
        """Erweitert bestehende process_document Methode"""
        
        # 1. BESTEHENDE PIPELINE LÄUFT UNVERÄNDERT
        ocr_result = self.ocr_service.extract_text(document_id)
        ner_result = self.ner_service.extract_entities(ocr_result)
        
        # 2. NEUER AGENT-ROUTING-SCHRITT
        user_id = self._get_user_for_document(document_id)
        route, context = self.confidence_router.route_document(
            ner_result, user_id, self.batch_id
        )
        
        final_result = ner_result  # Default: Originales Ergebnis
        
        # 3. AGENT-VERARBEITUNG NUR BEI BEDARF
        if route in ['agent_verify', 'agent_extract']:
            final_result = self._process_with_agent(
                document_id, ner_result, route, user_id
            )
        
        # 4. ERGEBNIS SPEICHERN (erweiterte ExtractionResult)
        self._save_enhanced_result(document_id, final_result, route, context)
        
        return final_result
    
    def _process_with_agent(self, document_id: int, ner_result, route: str, user_id: int):
        """NEUE METHODE: Agent-Verarbeitung"""
        
        # Memory Context laden
        memory_service = MemoryService(user_id, self.batch_id)
        memory_context = {
            **memory_service.get_short_term_context(document_id),
            **memory_service.get_long_term_context()
        }
        
        # Document Context (OCR-Text)
        document_context = ner_result.ocr_text
        
        # Agent Enhancement
        agent_result = self.agent_service.enhance_extraction(
            ner_result, document_context, memory_context
        )
        
        # Learning: Agent-Ergebnis in Memory speichern
        memory_service.learn_from_extraction(document_id, ner_result, agent_result)
        
        # Merge mit originalem NER-Ergebnis
        enhanced_result = self._merge_results(ner_result, agent_result)
        
        return enhanced_result
    
    def _merge_results(self, ner_result, agent_result):
        """NEUE METHODE: NER + Agent Ergebnisse zusammenführen"""
        
        # Kopiere ursprüngliches Ergebnis
        enhanced_result = ner_result
        
        # Agent-Verbesserungen übernehmen
        enhanced_result.extracted_data['entities'] = [
            entity.model_dump() for entity in agent_result.entities
        ]
        
        # Metadata hinzufügen
        enhanced_result.agent_enhanced = True
        enhanced_result.agent_confidence = agent_result.confidence
        enhanced_result.requires_review = agent_result.needs_review
        enhanced_result.review_reasons = agent_result.review_reasons
        
        return enhanced_result
    
    def _save_enhanced_result(self, document_id: int, result, route: str, context: Dict):
        """ERWEITERT bestehende Speicher-Logik"""
        
        # Bestehende ExtractionResult Speicherung bleibt unverändert
        # ... existing save logic ...
        
        # NEUE FELDER SETZEN
        result.agent_enhanced = route in ['agent_verify', 'agent_extract']
        result.requires_review = route == 'human' or (
            hasattr(result, 'review_reasons') and result.review_reasons
        )
        
        result.save()
        
        # Optional: Metrics logging
        self._log_agent_metrics(document_id, route, context)
```

### 3.2 API-Erweiterungen (api/v1/agent_views.py)

```python
# api/v1/agent_views.py - NEUE DATEI
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from documents.models import DocumentMemory, KnowledgeGraph
from extraction.services.memory_service import MemoryService

class AgentViewSet(viewsets.ModelViewSet):
    """Agent-spezifische API Endpoints"""
    
    @action(detail=False, methods=['get'])
    def memory_stats(self, request):
        """Memory-Statistiken für Dashboard"""
        user = request.user
        
        # Short-term Memory Stats
        session_memories = DocumentMemory.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count()
        
        # Long-term Memory Stats  
        knowledge_items = KnowledgeGraph.objects.filter(user=user).count()
        top_entities = KnowledgeGraph.objects.filter(
            user=user
        ).order_by('-weight')[:10].values('source_entity', 'weight', 'occurrences')
        
        return Response({
            'session_memories': session_memories,
            'knowledge_items': knowledge_items,
            'top_entities': list(top_entities),
            'memory_efficiency': {
                'cache_hits': cache.get(f'cache_hits_{user.id}', 0),
                'total_queries': cache.get(f'total_queries_{user.id}', 0)
            }
        })
    
    @action(detail=False, methods=['post'])
    def train_pattern(self, request):
        """Manuell Pattern zu Memory hinzufügen"""
        user = request.user
        pattern_data = request.data
        
        # Validate pattern_data
        required_fields = ['source_entity', 'target_entity', 'relationship_type']
        if not all(field in pattern_data for field in required_fields):
            return Response(
                {'error': 'Missing required fields'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update KnowledgeGraph entry
        kg_item, created = KnowledgeGraph.objects.get_or_create(
            user=user,
            source_entity=pattern_data['source_entity'],
            target_entity=pattern_data['target_entity'],
            relationship_type=pattern_data['relationship_type'],
            defaults={
                'confidence': pattern_data.get('confidence', 0.9),
                'weight': pattern_data.get('weight', 1.0),
                'occurrences': 1,
                'metadata': pattern_data.get('metadata', {})
            }
        )
        
        if not created:
            kg_item.occurrences += 1
            kg_item.weight = min(10.0, kg_item.weight + 0.5)
            kg_item.save()
        
        return Response({
            'status': 'created' if created else 'updated',
            'knowledge_item_id': kg_item.id
        })

# api/v1/urls.py - ERWEITERN
from .agent_views import AgentViewSet

router.register(r'agent', AgentViewSet, basename='agent')
```

### 3.3 Settings-Erweiterungen

```python
# settings/base.py - HINZUFÜGEN
# Gemini Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-1.5-flash'

# Agent Configuration
AGENT_SETTINGS = {
    'CONFIDENCE_THRESHOLDS': {
        'auto_accept': 0.92,
        'agent_verify': 0.80,
        'agent_extract': 0.70,
    },
    'FIELD_WEIGHTS': {
        'amount': 3.0,
        'date': 2.5,
        'gaeb_position': 2.5,
        'vendor_name': 2.0,
    },
    'MEMORY_TTL': 3600,  # Session Memory TTL in seconds
    'MAX_CONTEXT_LENGTH': 2000,  # Max chars für Context
}

# Cache für Memory Service
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 3600,
    }
}
```

---

## Phase 4: Testing & Monitoring (Woche 7-8)

### 4.1 Test-Strategie

```python
# tests/test_agent_integration.py - NEUE DATEI
from django.test import TestCase
from unittest.mock import patch, MagicMock
from extraction.services.agent_service import GeminiAgentService
from extraction.middleware.confidence_router import ConfidenceRouter

class AgentIntegrationTest(TestCase):
    
    def setUp(self):
        self.agent_service = GeminiAgentService()
        self.router = ConfidenceRouter()
    
    @patch('google.generativeai.GenerativeModel')
    def test_high_confidence_skips_agent(self, mock_gemini):
        """Test: Hohe Confidence -> Kein Agent"""
        extraction_result = self._create_high_confidence_result()
        
        should_use = self.agent_service.should_use_agent(extraction_result)
        self.assertFalse(should_use)
        
        # Gemini sollte nicht aufgerufen werden
        mock_gemini.assert_not_called()
    
    def test_low_confidence_routes_to_agent(self):
        """Test: Niedrige Confidence -> Agent-Route"""
        extraction_result = self._create_low_confidence_result()
        
        route, context = self.router.route_document(extraction_result, user_id=1)
        
        self.assertIn(route, ['agent_verify', 'agent_extract'])
        self.assertIn('confidence', context)
    
    def test_critical_fields_force_agent(self):
        """Test: Kritische Felder mit niedriger Confidence -> Agent"""
        extraction_result = self._create_result_with_low_critical_fields()
        
        route, context = self.router.route_document(extraction_result, user_id=1)
        
        self.assertEqual(route, 'agent_extract')
        self.assertIn('critical_fields_low', context['reason'])
    
    def _create_high_confidence_result(self):
        """Helper: High-Confidence ExtractionResult"""
        from documents.models import ExtractionResult, Document
        
        result = ExtractionResult()
        result.confidence_scores = {
            'amount': 0.95,
            'date': 0.93,
            'vendor_name': 0.92,
            'gaeb_position': 0.94
        }
        result.extracted_data = {
            'entities': [
                {'type': 'AMOUNT', 'value': '1.250,50', 'confidence': 0.95},
                {'type': 'DATE', 'value': '15.11.2025', 'confidence': 0.93}
            ]
        }
        return result

# Testausführung
# python manage.py test tests.test_agent_integration -v 2
```

### 4.2 Monitoring & Metriken

```python
# monitoring/agent_metrics.py - NEUE DATEI
from django.core.management.base import BaseCommand
from documents.models import ExtractionResult, Batch
from django.utils import timezone
from datetime import timedelta

class AgentMetrics:
    """Sammelt Agent-Performance-Metriken"""
    
    def get_daily_stats(self, days=7):
        """Agent-Nutzungs-Statistiken der letzten N Tage"""
        since = timezone.now() - timedelta(days=days)
        
        total_docs = ExtractionResult.objects.filter(
            created_at__gte=since
        ).count()
        
        agent_enhanced = ExtractionResult.objects.filter(
            created_at__gte=since,
            agent_enhanced=True
        ).count()
        
        requires_review = ExtractionResult.objects.filter(
            created_at__gte=since,
            requires_review=True
        ).count()
        
        return {
            'total_documents': total_docs,
            'agent_enhanced': agent_enhanced,
            'agent_usage_rate': (agent_enhanced / total_docs * 100) if total_docs > 0 else 0,
            'review_rate': (requires_review / total_docs * 100) if total_docs > 0 else 0,
            'stp_rate': ((total_docs - requires_review) / total_docs * 100) if total_docs > 0 else 0
        }
    
    def get_confidence_improvement(self):
        """Misst Confidence-Verbesserung durch Agent"""
        agent_results = ExtractionResult.objects.filter(
            agent_enhanced=True,
            agent_confidence__isnull=False
        ).values('confidence', 'agent_confidence')
        
        improvements = []
        for result in agent_results:
            original = result['confidence']
            enhanced = result['agent_confidence']
            if original > 0:
                improvement = (enhanced - original) / original * 100
                improvements.append(improvement)
        
        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            return {
                'average_improvement_percent': round(avg_improvement, 2),
                'samples': len(improvements)
            }
        
        return {'average_improvement_percent': 0, 'samples': 0}

# Management Command für tägliche Metriken
# management/commands/collect_agent_metrics.py
class Command(BaseCommand):
    help = 'Collect daily agent metrics'
    
    def handle(self, *args, **options):
        metrics = AgentMetrics()
        stats = metrics.get_daily_stats()
        
        self.stdout.write(f"Agent Usage Rate: {stats['agent_usage_rate']:.1f}%")
        self.stdout.write(f"STP Rate: {stats['stp_rate']:.1f}%")
        self.stdout.write(f"Review Rate: {stats['review_rate']:.1f}%")
        
        # Optional: Send to monitoring system
        # send_to_prometheus(stats)
```

### 4.3 Cost Monitoring (Gemini Flash)

```python
# monitoring/cost_tracking.py - NEUE DATEI
from django.db import models
from decimal import Decimal

class GeminiUsageLog(models.Model):
    """Tracking für Gemini API Kosten"""
    
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    document_id = models.UUIDField()
    model_name = models.CharField(max_length=50, default='gemini-1.5-flash')
    
    # Token-Verbrauch
    input_tokens = models.IntegerField()
    output_tokens = models.IntegerField()
    
    # Kosten (Gemini Flash: $0.075 / 1M input, $0.30 / 1M output)
    input_cost = models.DecimalField(max_digits=10, decimal_places=6)
    output_cost = models.DecimalField(max_digits=10, decimal_places=6)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6)
    
    # Context
    route_type = models.CharField(max_length=20)  # agent_verify/agent_extract
    processing_time_ms = models.IntegerField()
    cache_hit = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

class CostTracker:
    """Kostenverfolgung für Gemini Flash 1.5"""
    
    GEMINI_FLASH_PRICES = {
        'input_per_1m': Decimal('0.075'),   # $0.075 per 1M input tokens
        'output_per_1m': Decimal('0.30')    # $0.30 per 1M output tokens
    }
    
    def log_usage(self, user_id: int, document_id: str, 
                  input_tokens: int, output_tokens: int,
                  route_type: str, processing_time_ms: int,
                  cache_hit: bool = False):
        """Log Gemini API usage für Cost-Tracking"""
        
        input_cost = (Decimal(input_tokens) / 1_000_000) * self.GEMINI_FLASH_PRICES['input_per_1m']
        output_cost = (Decimal(output_tokens) / 1_000_000) * self.GEMINI_FLASH_PRICES['output_per_1m']
        total_cost = input_cost + output_cost
        
        GeminiUsageLog.objects.create(
            user_id=user_id,
            document_id=document_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            route_type=route_type,
            processing_time_ms=processing_time_ms,
            cache_hit=cache_hit
        )
        
        return total_cost
    
    def get_monthly_cost(self, user_id: int) -> Dict:
        """Monatliche Kosten pro User"""
        current_month = timezone.now().replace(day=1)
        
        monthly_logs = GeminiUsageLog.objects.filter(
            user_id=user_id,
            created_at__gte=current_month
        )
        
        total_cost = monthly_logs.aggregate(
            total=models.Sum('total_cost')
        )['total'] or Decimal('0')
        
        call_count = monthly_logs.count()
        avg_cost_per_call = total_cost / call_count if call_count > 0 else Decimal('0')
        
        cache_hit_rate = monthly_logs.filter(cache_hit=True).count() / call_count if call_count > 0 else 0
        
        return {
            'total_cost_usd': float(total_cost),
            'api_calls': call_count,
            'avg_cost_per_call': float(avg_cost_per_call),
            'cache_hit_rate_percent': cache_hit_rate * 100
        }
```

---

## Deployment & Konfiguration

### Environment Setup

```bash
# .env Ergänzungen
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Redis für Memory Caching
REDIS_URL=redis://localhost:6379/1

# Agent Settings
AGENT_ENABLED=True
AGENT_MAX_COST_PER_MONTH=50.00  # USD
AGENT_TIMEOUT_SECONDS=30
```

### Migrations ausführen

```bash
# Database Migration
python manage.py makemigrations documents
python manage.py migrate

# Test Setup
python manage.py test tests.test_agent_integration

# Metrics sammeln
python manage.py collect_agent_metrics
```

### Requirements erweitern

```python
# requirements.txt HINZUFÜGEN
google-generativeai>=0.3.0
pydantic>=2.0.0
django-redis>=5.4.0
redis>=5.0.0
```

---

## Erfolgs-Metriken & ROI

### Quick Wins Tracking (nach 4 Wochen)

| Metrik | Baseline | Ziel | Messung |
|--------|----------|------|---------|
| **NER-Accuracy** | 92% | 96-98% | `python manage.py collect_agent_metrics` |
| **STP-Rate** | 70% | 85% | Auto-freigegebene Dokumente / Gesamt |
| **Agent-Usage-Rate** | 0% | 15-25% | Agent-Enhanced / Total Documents |
| **Review-Rate** | 30% | 10-15% | Manual Review / Total Documents |
| **Monthly LLM Cost** | 0€ | <10€ | Gemini Flash Token-Kosten |

### Expected Performance (8 Wochen)

**Bei 260 Dokumenten/Monat:**
- **220 Dokumente (85%):** Straight-Through-Processing ohne Agent
- **40 Dokumente (15%):** Agent-Enhancement
- **Gemini Flash Kosten:** ~25.000 Input + 5.000 Output Tokens/Dokument = **~5-8€/Monat**
- **Review-Zeit Reduktion:** Von 5-10 min auf 1-2 min = **~900€ Arbeitszeit-Einsparung/Monat**

### Break-Even-Analyse

- **Entwicklungsaufwand:** ~40h (1 Woche Claude Code)
- **Monthly Operational Cost:** <10€ LLM + 0€ Infrastructure (PostgreSQL/Redis bereits vorhanden)
- **Monthly Savings:** ~900€ (reduzierte Review-Zeit)
- **ROI:** **Break-even nach 1-2 Tagen Betrieb**

---

## Nächste Schritte

### Phase 1 (Woche 1-2): Foundation
1. ✅ Models erweitern mit Migrations
2. ✅ GeminiAgentService implementieren
3. ✅ ConfidenceRouter implementieren
4. ✅ Basis-Tests schreiben

### Phase 2 (Woche 3-4): Integration
1. ✅ BatchProcessor erweitern
2. ✅ Memory Service implementieren
3. ✅ API-Endpoints hinzufügen
4. ✅ Cost Tracking implementieren

### Phase 3 (Woche 5-6): Optimierung
1. ✅ Semantic Caching mit GPTCache
2. ✅ Field-spezifische Schwellenwerte tunen
3. ✅ Batch-API für Gemini (falls verfügbar)
4. ✅ A/B Testing Setup

### Phase 4 (Woche 7-8): Production
1. ✅ Performance Monitoring
2. ✅ Cost Alerts implementieren
3. ✅ User Training für Review-UI
4. ✅ Documentation & Handover

---

**Implementierung mit Claude Code:**
Dieser Leitfaden ist für sequentielle Umsetzung mit Claude Code optimiert. Jede Phase kann separat implementiert werden, ohne bestehende Funktionalität zu brechen.

**Backup-Strategie:**
Alle Änderungen sind additiv. Bei Problemen kann Agent-Funktionalität via `AGENT_ENABLED=False` deaktiviert werden, System läuft weiter mit bestehender Pipeline.
