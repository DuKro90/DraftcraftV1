"""Dual-layer memory service for agentic RAG pattern tracking."""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import Avg
from django.utils import timezone

from documents.agent_models import DocumentMemory, KnowledgeGraph

logger = logging.getLogger(__name__)


class MemoryServiceError(Exception):
    """Exception for memory service errors."""
    pass


class MemoryService:
    """
    Manages dual-layer memory for agentic RAG processing.

    Layer 1 (Short-term): Redis cache with 1-hour TTL
    - Session patterns
    - Recent vendor names, materials, amounts
    - Rapidly changing contextual data

    Layer 2 (Long-term): PostgreSQL KnowledgeGraph
    - Entity relationships (vendor → contact, material → supplier)
    - Persistent patterns learned over time
    - Co-occurrence statistics
    """

    # Cache key prefixes
    PATTERN_CACHE_PREFIX = "pattern:"
    CONTEXT_CACHE_PREFIX = "context:"
    MEMORY_TTL_SECONDS = 3600  # 1 hour

    # Pattern types
    PATTERN_TYPES = [
        'layout', 'vendor', 'amount', 'date',
        'gaeb', 'material', 'contact', 'custom'
    ]

    def __init__(self, user: User):
        """Initialize memory service for specific user.

        Args:
            user: Django User instance

        Raises:
            MemoryServiceError: If user is None
        """
        if not user:
            raise MemoryServiceError("User is required for memory service")
        self.user = user

    # ===== SHORT-TERM MEMORY (Redis Cache) =====

    def store_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any]
    ) -> None:
        """
        Store pattern in short-term memory (Redis cache).

        Args:
            pattern_type: Type of pattern (vendor, amount, material, etc.)
            pattern_data: Pattern data to store

        Raises:
            MemoryServiceError: If pattern_type is invalid
        """
        if pattern_type not in self.PATTERN_TYPES:
            raise MemoryServiceError(f"Invalid pattern type: {pattern_type}")

        cache_key = f"{self.PATTERN_CACHE_PREFIX}{self.user.id}:{pattern_type}"

        try:
            cache.set(
                cache_key,
                {
                    'pattern_data': pattern_data,
                    'stored_at': timezone.now().isoformat(),
                },
                timeout=self.MEMORY_TTL_SECONDS
            )
            logger.debug(f"Stored pattern: {pattern_type} for user {self.user.id}")
        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
            # Don't raise - graceful degradation

    def get_pattern(self, pattern_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve pattern from short-term memory.

        Args:
            pattern_type: Type of pattern to retrieve

        Returns:
            Pattern data if found, None otherwise
        """
        cache_key = f"{self.PATTERN_CACHE_PREFIX}{self.user.id}:{pattern_type}"

        try:
            cached = cache.get(cache_key)
            if cached:
                return cached.get('pattern_data')
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve pattern: {e}")
            return None

    def store_context(
        self,
        context_key: str,
        context_data: Dict[str, Any]
    ) -> None:
        """
        Store session context in short-term memory.

        Args:
            context_key: Context identifier
            context_data: Context data to store
        """
        cache_key = f"{self.CONTEXT_CACHE_PREFIX}{self.user.id}:{context_key}"

        try:
            cache.set(cache_key, context_data, timeout=self.MEMORY_TTL_SECONDS)
            logger.debug(f"Stored context: {context_key} for user {self.user.id}")
        except Exception as e:
            logger.error(f"Failed to store context: {e}")

    def get_context(self, context_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session context from short-term memory.

        Args:
            context_key: Context identifier

        Returns:
            Context data if found, None otherwise
        """
        cache_key = f"{self.CONTEXT_CACHE_PREFIX}{self.user.id}:{context_key}"

        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return None

    def clear_patterns(self) -> None:
        """Clear all session patterns from short-term memory."""
        try:
            for pattern_type in self.PATTERN_TYPES:
                cache_key = f"{self.PATTERN_CACHE_PREFIX}{self.user.id}:{pattern_type}"
                cache.delete(cache_key)
            logger.info(f"Cleared patterns for user {self.user.id}")
        except Exception as e:
            logger.error(f"Failed to clear patterns: {e}")

    # ===== LONG-TERM MEMORY (PostgreSQL KnowledgeGraph) =====

    def learn_relationship(
        self,
        source_entity: str,
        target_entity: str,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentMemory:
        """
        Learn and store entity relationship in long-term memory.

        Uses upsert pattern to update confidence on repeated observations.

        Args:
            source_entity: Source entity (e.g., vendor name)
            target_entity: Target entity (e.g., contact person)
            relationship_type: Type of relationship
            metadata: Optional metadata

        Returns:
            KnowledgeGraph instance
        """
        if not metadata:
            metadata = {}

        try:
            # Get or create relationship
            kg, created = KnowledgeGraph.objects.get_or_create(
                user=self.user,
                source_entity=source_entity,
                target_entity=target_entity,
                relationship_type=relationship_type,
                defaults={
                    'confidence': 0.7,
                    'weight': 1.0,
                    'occurrences': 1,
                    'metadata': metadata,
                }
            )

            if not created:
                # Update existing relationship
                kg.occurrences += 1
                # Increase confidence on repeated observations (up to 0.99)
                kg.confidence = min(kg.confidence + 0.05, 0.99)
                kg.metadata.update(metadata)
                kg.save()
                logger.debug(
                    f"Updated relationship: {source_entity} → {target_entity} "
                    f"(occurrences: {kg.occurrences})"
                )
            else:
                logger.debug(
                    f"Learned relationship: {source_entity} → {target_entity}"
                )

            return kg

        except Exception as e:
            logger.error(f"Failed to learn relationship: {e}")
            raise MemoryServiceError(f"Failed to learn relationship: {e}")

    def query_related_entities(
        self,
        entity: str,
        relationship_type: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Query related entities from long-term memory.

        Args:
            entity: Source entity to find relations for
            relationship_type: Optional relationship type filter
            min_confidence: Minimum confidence threshold

        Returns:
            List of (entity, confidence) tuples sorted by confidence
        """
        try:
            query = KnowledgeGraph.objects.filter(
                user=self.user,
                source_entity=entity,
                confidence__gte=min_confidence
            )

            if relationship_type:
                query = query.filter(relationship_type=relationship_type)

            results = [
                (kg.target_entity, kg.confidence)
                for kg in query.order_by('-confidence')
            ]

            return results

        except Exception as e:
            logger.error(f"Failed to query relationships: {e}")
            return []

    def get_document_patterns(
        self,
        pattern_type: Optional[str] = None,
        days_back: int = 7
    ) -> List[DocumentMemory]:
        """
        Get document patterns from long-term memory.

        Args:
            pattern_type: Optional pattern type filter
            days_back: Only return patterns from last N days

        Returns:
            List of DocumentMemory instances
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days_back)

            query = DocumentMemory.objects.filter(
                user=self.user,
                last_used__gte=cutoff_date
            )

            if pattern_type:
                query = query.filter(pattern_type=pattern_type)

            return list(query.order_by('-last_used'))

        except Exception as e:
            logger.error(f"Failed to get document patterns: {e}")
            return []

    def record_pattern_success(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        success: bool
    ) -> None:
        """
        Record pattern usage and success for learning.

        Args:
            pattern_type: Type of pattern
            pattern_data: Pattern data
            success: Whether pattern was successful
        """
        try:
            pattern_json = json.dumps(pattern_data, sort_keys=True, default=str)

            pattern, created = DocumentMemory.objects.get_or_create(
                user=self.user,
                pattern_type=pattern_type,
                pattern_data=pattern_data,
                defaults={
                    'confidence': 0.7,
                    'usage_count': 0,
                    'success_count': 0,
                }
            )

            pattern.usage_count += 1
            if success:
                pattern.success_count += 1
                # Increase confidence on success
                pattern.confidence = min(pattern.confidence + 0.02, 0.98)
            else:
                # Decrease confidence on failure
                pattern.confidence = max(pattern.confidence - 0.05, 0.3)

            pattern.save(update_fields=['usage_count', 'success_count', 'confidence', 'last_used'])

            logger.debug(
                f"Recorded pattern success: {pattern_type} "
                f"(success_rate: {pattern.success_rate:.2%})"
            )

        except Exception as e:
            logger.error(f"Failed to record pattern success: {e}")

    # ===== MEMORY SYNTHESIS =====

    def synthesize_context(
        self,
        recent_docs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize complete context from both memory layers.

        Args:
            recent_docs: Optional list of recent document data

        Returns:
            Synthesized context dictionary for agent use
        """
        try:
            context = {
                'short_term': {
                    'patterns': {}
                },
                'long_term': {
                    'relationships': {},
                    'learned_patterns': {}
                },
                'timestamp': timezone.now().isoformat(),
            }

            # Short-term patterns
            for pattern_type in self.PATTERN_TYPES:
                pattern = self.get_pattern(pattern_type)
                if pattern:
                    context['short_term']['patterns'][pattern_type] = pattern

            # Long-term relationships (high confidence)
            kg_entries = KnowledgeGraph.objects.filter(
                user=self.user,
                confidence__gte=0.75
            ).order_by('-confidence')[:10]

            for kg in kg_entries:
                key = f"{kg.source_entity}→{kg.target_entity}"
                context['long_term']['relationships'][key] = {
                    'type': kg.relationship_type,
                    'confidence': kg.confidence,
                    'occurrences': kg.occurrences,
                }

            # High-success patterns
            doc_patterns = self.get_document_patterns(days_back=30)
            for pattern in doc_patterns:
                if pattern.success_rate > 0.8:
                    context['long_term']['learned_patterns'][pattern.pattern_type] = {
                        'confidence': pattern.confidence,
                        'success_rate': pattern.success_rate,
                        'usage_count': pattern.usage_count,
                    }

            return context

        except Exception as e:
            logger.error(f"Failed to synthesize context: {e}")
            return {'error': str(e), 'timestamp': timezone.now().isoformat()}

    def cleanup_old_memory(self, days_old: int = 90) -> Tuple[int, int]:
        """
        Clean up old memory entries.

        Args:
            days_old: Delete entries older than N days

        Returns:
            Tuple of (deleted_kg_count, deleted_pattern_count)
        """
        cutoff_date = timezone.now() - timedelta(days=days_old)

        try:
            # Delete old knowledge graph entries
            kg_deleted, _ = KnowledgeGraph.objects.filter(
                user=self.user,
                last_seen__lt=cutoff_date,
                confidence__lt=0.5  # Only delete low-confidence old entries
            ).delete()

            # Delete old unused patterns
            pattern_deleted, _ = DocumentMemory.objects.filter(
                user=self.user,
                last_used__lt=cutoff_date,
                success_count=0  # Only delete never-successful old entries
            ).delete()

            logger.info(
                f"Memory cleanup: deleted {kg_deleted} KG entries, "
                f"{pattern_deleted} patterns"
            )

            return kg_deleted, pattern_deleted

        except Exception as e:
            logger.error(f"Failed to cleanup memory: {e}")
            return 0, 0

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about user's memory usage."""
        try:
            kg_count = KnowledgeGraph.objects.filter(user=self.user).count()
            pattern_count = DocumentMemory.objects.filter(user=self.user).count()

            # Average confidence
            kg_avg_conf = KnowledgeGraph.objects.filter(
                user=self.user
            ).aggregate(models.Avg('confidence'))['confidence__avg'] or 0.0

            pattern_avg_conf = DocumentMemory.objects.filter(
                user=self.user
            ).aggregate(models.Avg('confidence'))['confidence__avg'] or 0.0

            return {
                'knowledge_graph_entries': kg_count,
                'document_patterns': pattern_count,
                'avg_kg_confidence': round(kg_avg_conf, 3),
                'avg_pattern_confidence': round(pattern_avg_conf, 3),
                'timestamp': timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {'error': str(e)}
