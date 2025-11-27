"""Unit tests for Phase 2 agentic RAG services."""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.cache import cache
from django.utils import timezone

from extraction.services.gemini_agent_service import (
    GeminiAgentService,
    GeminiAgentError
)
from extraction.services.memory_service import (
    MemoryService,
    MemoryServiceError
)
from extraction.services.confidence_router import (
    ConfidenceRouter,
    RouteType,
    ComplexityLevel
)
from extraction.services.cost_tracker import (
    CostTracker,
    BudgetStatus,
    CostTrackerError
)
from documents.agent_models import (
    DocumentMemory,
    KnowledgeGraph,
    GeminiUsageLog,
    UserAgentBudget
)


@pytest.mark.django_db
class TestGeminiAgentService(TestCase):
    """Test Gemini agent service with mock and real modes."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )

    def test_initialization_mock_mode(self):
        """Test service initializes in mock mode when USE_MOCK_GEMINI=True."""
        with patch('extraction.services.gemini_agent_service.settings') as mock_settings:
            mock_settings.GEMINI_MODEL = 'gemini-1.5-flash'
            mock_settings.USE_MOCK_GEMINI = True
            mock_settings.GEMINI_API_KEY = ''

            service = GeminiAgentService({})
            assert service.use_mock is True
            assert service.client is None

    def test_initialization_api_mode_no_key(self):
        """Test service falls back to mock when API key missing."""
        with patch('extraction.services.gemini_agent_service.settings') as mock_settings:
            mock_settings.GEMINI_MODEL = 'gemini-1.5-flash'
            mock_settings.USE_MOCK_GEMINI = False
            mock_settings.GEMINI_API_KEY = ''

            service = GeminiAgentService({})
            assert service.use_mock is True

    def test_extract_with_agent_mock_mode(self):
        """Test extraction in mock mode."""
        with patch('extraction.services.gemini_agent_service.settings') as mock_settings:
            mock_settings.GEMINI_MODEL = 'gemini-1.5-flash'
            mock_settings.USE_MOCK_GEMINI = True
            mock_settings.GEMINI_API_KEY = ''

            service = GeminiAgentService({})

            result, tokens, cost = service.extract_with_agent(
                extracted_text="Test document text",
                current_fields={'vendor_name': 'Test Vendor'},
                confidence_scores={'vendor_name': 0.85}
            )

            assert 'extracted_fields' in result
            assert 'metadata' in result
            assert tokens > 0
            assert isinstance(cost, Decimal)

    def test_token_estimation(self):
        """Test token estimation calculation."""
        with patch('extraction.services.gemini_agent_service.settings') as mock_settings:
            mock_settings.GEMINI_MODEL = 'gemini-1.5-flash'
            mock_settings.USE_MOCK_GEMINI = True
            mock_settings.GEMINI_API_KEY = ''

            service = GeminiAgentService({})

            # 100 chars ≈ 25 tokens at 0.25 ratio
            tokens = service._estimate_tokens('x' * 100)
            assert 20 <= tokens <= 30

    def test_cost_calculation(self):
        """Test cost calculation from tokens."""
        with patch('extraction.services.gemini_agent_service.settings') as mock_settings:
            mock_settings.GEMINI_MODEL = 'gemini-1.5-flash'
            mock_settings.USE_MOCK_GEMINI = True
            mock_settings.GEMINI_API_KEY = ''
            mock_settings.GEMINI_BUDGET_CONFIG = {
                'MODEL_PRICING': {
                    'gemini-1.5-flash': {
                        'input_per_1m_tokens': 0.075,
                        'output_per_1m_tokens': 0.30,
                    }
                }
            }

            service = GeminiAgentService({})

            # 1000 input + 500 output tokens
            cost = service._calculate_cost(1000, 500)
            assert isinstance(cost, Decimal)
            assert cost > Decimal('0')

    def test_parse_gemini_response(self):
        """Test JSON parsing from Gemini response."""
        with patch('extraction.services.gemini_agent_service.settings') as mock_settings:
            mock_settings.GEMINI_MODEL = 'gemini-1.5-flash'
            mock_settings.USE_MOCK_GEMINI = True
            mock_settings.GEMINI_API_KEY = ''

            service = GeminiAgentService({})

            response = '{"confidence": 0.95, "extracted_fields": {"amount": 100}}'
            result = service._parse_gemini_response(response)

            assert result['confidence'] == 0.95
            assert result['extracted_fields']['amount'] == 100

    def test_parse_gemini_response_with_extra_text(self):
        """Test JSON parsing when response has extra text."""
        with patch('extraction.services.gemini_agent_service.settings') as mock_settings:
            mock_settings.GEMINI_MODEL = 'gemini-1.5-flash'
            mock_settings.USE_MOCK_GEMINI = True
            mock_settings.GEMINI_API_KEY = ''

            service = GeminiAgentService({})

            response = 'Here is the result: {"confidence": 0.92} Please use this data.'
            result = service._parse_gemini_response(response)

            assert result['confidence'] == 0.92


@pytest.mark.django_db
class TestMemoryService(TestCase):
    """Test memory service with short and long-term layers."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        self.memory_service = MemoryService(self.user)

    def test_initialization_requires_user(self):
        """Test service initialization requires user."""
        with pytest.raises(MemoryServiceError):
            MemoryService(None)

    def test_store_and_retrieve_pattern(self):
        """Test storing and retrieving short-term patterns."""
        pattern_data = {'vendor_name': 'Test GmbH', 'region': 'Bayern'}

        self.memory_service.store_pattern('vendor', pattern_data)
        retrieved = self.memory_service.get_pattern('vendor')

        assert retrieved == pattern_data

    def test_store_and_retrieve_context(self):
        """Test storing and retrieving session context."""
        context = {'session_id': '123', 'documents_count': 5}

        self.memory_service.store_context('session_001', context)
        retrieved = self.memory_service.get_context('session_001')

        assert retrieved == context

    def test_learn_relationship(self):
        """Test learning entity relationships."""
        kg = self.memory_service.learn_relationship(
            source_entity='Müller GmbH',
            target_entity='Hans Müller',
            relationship_type='vendor_to_contact'
        )

        assert kg.source_entity == 'Müller GmbH'
        assert kg.target_entity == 'Hans Müller'
        assert kg.occurrences == 1

    def test_relationship_confidence_increases_on_repeat(self):
        """Test relationship confidence increases with repetition."""
        source = 'Müller GmbH'
        target = 'Hans Müller'

        kg1 = self.memory_service.learn_relationship(source, target, 'vendor_to_contact')
        initial_confidence = kg1.confidence

        kg2 = self.memory_service.learn_relationship(source, target, 'vendor_to_contact')
        updated_confidence = kg2.confidence

        assert updated_confidence > initial_confidence
        assert kg2.occurrences == 2

    def test_query_related_entities(self):
        """Test querying related entities."""
        self.memory_service.learn_relationship(
            'Müller GmbH',
            'Hans Müller',
            'vendor_to_contact'
        )
        self.memory_service.learn_relationship(
            'Müller GmbH',
            'contact@mueller.de',
            'vendor_to_contact'
        )

        related = self.memory_service.query_related_entities('Müller GmbH')

        assert len(related) == 2
        assert any(entity[0] == 'Hans Müller' for entity in related)

    def test_record_pattern_success(self):
        """Test recording pattern success."""
        pattern_data = {'format': 'DD.MM.YYYY'}

        self.memory_service.record_pattern_success(
            'date',
            pattern_data,
            success=True
        )

        pattern = DocumentMemory.objects.filter(
            user=self.user,
            pattern_type='date'
        ).first()

        assert pattern is not None
        assert pattern.success_count == 1
        assert pattern.usage_count == 1

    def test_pattern_confidence_increases_on_success(self):
        """Test pattern confidence increases on successful usage."""
        pattern_data = {'format': 'DD.MM.YYYY'}

        self.memory_service.record_pattern_success('date', pattern_data, success=True)
        pattern1 = DocumentMemory.objects.get(user=self.user, pattern_type='date')
        conf1 = pattern1.confidence

        self.memory_service.record_pattern_success('date', pattern_data, success=True)
        pattern2 = DocumentMemory.objects.get(user=self.user, pattern_type='date')
        conf2 = pattern2.confidence

        assert conf2 > conf1

    def test_pattern_confidence_decreases_on_failure(self):
        """Test pattern confidence decreases on failed usage."""
        pattern_data = {'format': 'DD.MM.YYYY'}

        self.memory_service.record_pattern_success('date', pattern_data, success=True)
        pattern1 = DocumentMemory.objects.get(user=self.user, pattern_type='date')
        conf1 = pattern1.confidence

        self.memory_service.record_pattern_success('date', pattern_data, success=False)
        pattern2 = DocumentMemory.objects.get(user=self.user, pattern_type='date')
        conf2 = pattern2.confidence

        assert conf2 < conf1

    def test_synthesize_context(self):
        """Test context synthesis from both memory layers."""
        self.memory_service.store_pattern('vendor', {'name': 'Test'})
        self.memory_service.learn_relationship('Vendor', 'Contact', 'vendor_to_contact')

        context = self.memory_service.synthesize_context()

        assert 'short_term' in context
        assert 'long_term' in context
        assert 'patterns' in context['short_term']
        assert 'relationships' in context['long_term']

    def test_cleanup_old_memory(self):
        """Test cleaning up old memory entries."""
        self.memory_service.learn_relationship('Old', 'Entity', 'custom')

        # Manually set old timestamp
        kg = KnowledgeGraph.objects.filter(user=self.user).first()
        kg.last_seen = timezone.now() - timezone.timedelta(days=100)
        kg.confidence = 0.3  # Low confidence
        kg.save()

        deleted_kg, deleted_patterns = self.memory_service.cleanup_old_memory(days_old=90)

        assert deleted_kg == 1

    def test_get_memory_stats(self):
        """Test getting memory statistics."""
        self.memory_service.learn_relationship('Vendor', 'Contact', 'vendor_to_contact')
        self.memory_service.record_pattern_success('vendor', {'name': 'Test'}, success=True)

        stats = self.memory_service.get_memory_stats()

        assert stats['knowledge_graph_entries'] >= 1
        assert stats['document_patterns'] >= 1
        assert 'avg_kg_confidence' in stats


@pytest.mark.django_db
class TestConfidenceRouter(TestCase):
    """Test intelligent routing based on confidence."""

    def setUp(self):
        """Set up test fixtures."""
        self.router = ConfidenceRouter()

    def test_auto_accept_route_high_confidence(self):
        """Test auto-accept route for high confidence."""
        extraction_result = {'vendor_name': 'Test', 'amount': 100}
        confidence_scores = {'vendor_name': 0.95, 'amount': 0.94}

        route, confidence, reasoning = self.router.route(
            extraction_result,
            confidence_scores
        )

        assert route == RouteType.AUTO_ACCEPT
        assert confidence > 0.90

    def test_agent_verify_route_borderline_confidence(self):
        """Test agent-verify route for borderline confidence."""
        extraction_result = {'vendor_name': 'Test', 'amount': 100}
        confidence_scores = {'vendor_name': 0.85, 'amount': 0.82}

        route, confidence, reasoning = self.router.route(
            extraction_result,
            confidence_scores
        )

        assert route == RouteType.AGENT_VERIFY

    def test_agent_extract_route_low_confidence(self):
        """Test agent-extract route for low confidence."""
        extraction_result = {'vendor_name': 'Test', 'amount': 100}
        confidence_scores = {'vendor_name': 0.72, 'amount': 0.70}

        route, confidence, reasoning = self.router.route(
            extraction_result,
            confidence_scores
        )

        assert route == RouteType.AGENT_EXTRACT

    def test_human_review_route_very_low_confidence(self):
        """Test human-review route for very low confidence."""
        extraction_result = {'vendor_name': 'Test', 'amount': 100}
        confidence_scores = {'vendor_name': 0.50, 'amount': 0.45}

        route, confidence, reasoning = self.router.route(
            extraction_result,
            confidence_scores
        )

        assert route == RouteType.HUMAN_REVIEW

    def test_weighted_confidence_calculation(self):
        """Test weighted confidence considers field weights."""
        extraction_result = {'amount': 100, 'notes': 'test'}
        # Amount has weight 3.0, notes has weight 0.5
        # (100 * 0.9 * 3.0 + 0.5 * 0.5) / (3.0 + 0.5) = 2.7025 / 3.5 = 0.772
        confidence_scores = {'amount': 0.90, 'notes': 0.50}

        route, confidence, reasoning = self.router.route(
            extraction_result,
            confidence_scores
        )

        # Should be weighted toward the high-confidence amount field
        assert confidence > 0.70

    def test_complexity_affects_routing(self):
        """Test that complexity affects routing decisions."""
        extraction_result = {
            'vendor_name': 'Test',
            'gaeb_position': '01.001',  # Indicates HIGH complexity
            'amount': 100
        }
        confidence_scores = {'vendor_name': 0.85, 'gaeb_position': 0.80, 'amount': 0.82}

        route, confidence, reasoning = self.router.route(
            extraction_result,
            confidence_scores
        )

        # Complex documents should require higher confidence
        assert any('complexity' in str(r).lower() for r in reasoning)

    def test_missing_critical_fields(self):
        """Test routing changes for missing critical fields."""
        extraction_result = {'vendor_name': 'Test'}  # Missing amount and date
        confidence_scores = {'vendor_name': 0.95}

        route, confidence, reasoning = self.router.route(
            extraction_result,
            confidence_scores
        )

        # Should downgrade despite high vendor confidence
        assert route != RouteType.AUTO_ACCEPT

    def test_batch_routing(self):
        """Test routing multiple documents."""
        documents = [
            {
                'extraction_result': {'amount': 100},
                'confidence_scores': {'amount': 0.95}
            },
            {
                'extraction_result': {'amount': 100},
                'confidence_scores': {'amount': 0.75}
            }
        ]

        routes = self.router.route_batch(documents)

        assert len(routes) == 2
        assert routes[0][0] == RouteType.AUTO_ACCEPT
        assert routes[1][0] == RouteType.AGENT_EXTRACT


@pytest.mark.django_db
class TestCostTracker(TestCase):
    """Test budget tracking and cost enforcement."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        self.tracker = CostTracker(self.user)

    def test_initialization_creates_budget_record(self):
        """Test that service creates budget record if missing."""
        budget = UserAgentBudget.objects.get(user=self.user)
        assert budget.monthly_budget_usd == Decimal('50.00')
        assert budget.status == BudgetStatus.ACTIVE.value

    def test_initialization_requires_user(self):
        """Test service initialization requires user."""
        with pytest.raises(CostTrackerError):
            CostTracker(None)

    def test_log_usage(self):
        """Test logging API usage."""
        log = self.tracker.log_usage(
            route_type='agent_verify',
            input_tokens=200,
            output_tokens=100,
            cost_usd=Decimal('0.00005'),
            confidence_before=0.75,
            confidence_after=0.85
        )

        assert log.user == self.user
        assert log.input_tokens == 200
        assert log.output_tokens == 100
        assert log.total_tokens == 300

    def test_check_budget_available(self):
        """Test checking budget availability."""
        can_afford, reason = self.tracker.check_budget_available(
            Decimal('10.00')
        )

        assert can_afford is True

    def test_check_budget_insufficient(self):
        """Test budget insufficient check."""
        # Exhaust budget
        budget = UserAgentBudget.objects.get(user=self.user)
        budget.current_month_cost_usd = budget.monthly_budget_usd
        budget.save()

        can_afford, reason = self.tracker.check_budget_available(
            Decimal('1.00')
        )

        assert can_afford is False

    def test_enforce_budget_updates_status(self):
        """Test budget enforcement updates status."""
        self.tracker.enforce_budget(Decimal('45.00'))

        budget = UserAgentBudget.objects.get(user=self.user)

        assert budget.current_month_cost_usd == Decimal('45.00')

    def test_enforce_budget_sets_warning_status(self):
        """Test budget status changes to warning at threshold."""
        budget = UserAgentBudget.objects.get(user=self.user)
        budget.alert_threshold_percent = 80

        self.tracker.enforce_budget(Decimal('40.00'))

        budget.refresh_from_db()
        assert budget.status == BudgetStatus.WARNING.value

    def test_enforce_budget_pauses_at_limit(self):
        """Test budget is paused when limit reached."""
        self.tracker.enforce_budget(Decimal('50.00'))

        budget = UserAgentBudget.objects.get(user=self.user)
        assert budget.status == BudgetStatus.PAUSED.value

    def test_reset_monthly_budget(self):
        """Test monthly budget reset."""
        budget = UserAgentBudget.objects.get(user=self.user)
        budget.current_month_cost_usd = Decimal('45.00')
        budget.status = BudgetStatus.WARNING.value
        budget.save()

        self.tracker.reset_monthly_budget()

        budget.refresh_from_db()
        assert budget.current_month_cost_usd == Decimal('0.00')
        assert budget.status == BudgetStatus.ACTIVE.value

    def test_get_current_budget_status(self):
        """Test getting budget status."""
        self.tracker.enforce_budget(Decimal('15.00'))

        status = self.tracker.get_current_budget_status()

        assert status['budget_used_percent'] == 30.0
        assert status['budget_remaining_usd'] == 35.0

    def test_get_usage_statistics(self):
        """Test usage statistics calculation."""
        self.tracker.log_usage(
            route_type='agent_verify',
            input_tokens=200,
            output_tokens=100,
            cost_usd=Decimal('0.00005')
        )

        stats = self.tracker.get_usage_statistics(days_back=30)

        assert stats['total_calls'] == 1
        assert stats['total_tokens'] == 300

    def test_forecast_budget(self):
        """Test budget forecasting."""
        # Create several log entries
        for _ in range(5):
            self.tracker.log_usage(
                route_type='agent_verify',
                input_tokens=200,
                output_tokens=100,
                cost_usd=Decimal('0.00005')
            )

        forecast = self.tracker.forecast_budget()

        assert 'projected_monthly_cost_usd' in forecast
        assert 'budget_sufficient' in forecast
