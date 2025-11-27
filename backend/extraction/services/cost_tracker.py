"""Budget tracking and cost enforcement service for Gemini API usage."""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

from documents.agent_models import GeminiUsageLog, UserAgentBudget

logger = logging.getLogger(__name__)


class BudgetStatus(Enum):
    """Budget status indicators."""
    ACTIVE = "active"
    WARNING = "warning"
    PAUSED = "paused"
    DISABLED = "disabled"


class CostTrackerError(Exception):
    """Exception for cost tracking errors."""
    pass


class CostTracker:
    """
    Tracks API costs and enforces budget limits.

    Features:
    - Per-user monthly budget tracking
    - Real-time cost enforcement (prevents overspend)
    - Budget alerts at configurable thresholds
    - Cost estimation and forecasting
    - Detailed usage logging per API call
    """

    # Budget reset frequency
    BUDGET_RESET_FREQUENCY = "monthly"  # Reset on 1st of month
    ALERT_EMAIL_TEMPLATE = "agent_budget_alert.txt"

    def __init__(self, user: User):
        """Initialize cost tracker for user.

        Args:
            user: Django User instance

        Raises:
            CostTrackerError: If user is None
        """
        if not user:
            raise CostTrackerError("User is required for cost tracker")

        self.user = user
        self._ensure_budget_record()

    def _ensure_budget_record(self) -> UserAgentBudget:
        """Ensure user has a budget record, create if missing."""
        budget, created = UserAgentBudget.objects.get_or_create(
            user=self.user,
            defaults={
                'monthly_budget_usd': Decimal('50.00'),
                'status': BudgetStatus.ACTIVE.value,
            }
        )

        if created:
            logger.info(f"Created budget record for user {self.user.id}")

        return budget

    def log_usage(
        self,
        route_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
        confidence_before: Optional[float] = None,
        confidence_after: Optional[float] = None,
        processing_time_ms: int = 0,
        document_id: Optional[str] = None,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GeminiUsageLog:
        """
        Log API usage for cost tracking and analysis.

        Args:
            route_type: Type of routing (auto_accept, agent_verify, agent_extract, human_review)
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            cost_usd: Cost in USD
            confidence_before: Extraction confidence before agent
            confidence_after: Extraction confidence after agent
            processing_time_ms: Processing time in milliseconds
            document_id: Optional document UUID
            cache_hit: Whether cache was hit
            metadata: Optional additional metadata

        Returns:
            GeminiUsageLog instance

        Raises:
            CostTrackerError: If logging fails
        """
        if not metadata:
            metadata = {}

        try:
            log = GeminiUsageLog.objects.create(
                user=self.user,
                route_type=route_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                input_cost_usd=self._calculate_input_cost(input_tokens),
                output_cost_usd=self._calculate_output_cost(output_tokens),
                total_cost_usd=cost_usd,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                processing_time_ms=processing_time_ms,
                document_id=document_id,
                cache_hit=cache_hit,
                metadata=metadata,
            )

            logger.debug(
                f"Logged API usage: route={route_type}, "
                f"tokens={input_tokens + output_tokens}, cost=${cost_usd}"
            )

            return log

        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
            raise CostTrackerError(f"Failed to log usage: {e}")

    def check_budget_available(
        self,
        estimated_cost_usd: Decimal
    ) -> Tuple[bool, str]:
        """
        Check if budget is available for a new API call.

        Args:
            estimated_cost_usd: Estimated cost of next call

        Returns:
            Tuple of (can_afford, reason_if_not)
        """
        budget = UserAgentBudget.objects.get(user=self.user)

        # Check if budget is disabled
        if budget.status in [BudgetStatus.PAUSED.value, BudgetStatus.DISABLED.value]:
            return False, f"Budget status: {budget.status}"

        # Check if enough budget remains
        remaining = budget.budget_remaining_usd
        if remaining < estimated_cost_usd:
            return False, f"Insufficient budget: ${remaining} < ${estimated_cost_usd}"

        # Check if approaching limit
        if budget.budget_used_percent >= 100:
            return False, "Monthly budget fully used"

        return True, "Budget available"

    def enforce_budget(
        self,
        cost_usd: Decimal
    ) -> Tuple[bool, str]:
        """
        Update budget after API call and enforce limits.

        This must be called after every API call to track spending.

        Args:
            cost_usd: Actual cost of API call

        Returns:
            Tuple of (success, message)
        """
        try:
            budget = UserAgentBudget.objects.select_for_update().get(
                user=self.user
            )

            # Update current month cost
            budget.current_month_cost_usd += cost_usd

            # Update status based on budget used
            percent_used = budget.budget_used_percent

            if percent_used >= 100:
                old_status = budget.status
                budget.status = BudgetStatus.PAUSED.value
                logger.warning(
                    f"User {self.user.id} budget exceeded (${budget.current_month_cost_usd}). "
                    f"Status changed from {old_status} to {budget.status}"
                )
            elif percent_used >= budget.alert_threshold_percent:
                old_status = budget.status
                budget.status = BudgetStatus.WARNING.value
                if old_status != BudgetStatus.WARNING.value:
                    logger.warning(
                        f"User {self.user.id} budget alert: {percent_used:.1f}% used"
                    )

            budget.save(update_fields=[
                'current_month_cost_usd',
                'status'
            ])

            message = (
                f"Budget updated: ${cost_usd} charged, "
                f"${budget.budget_remaining_usd} remaining"
            )

            return True, message

        except Exception as e:
            logger.error(f"Failed to enforce budget: {e}")
            return False, f"Budget enforcement failed: {e}"

    def reset_monthly_budget(self) -> bool:
        """
        Reset monthly budget (typically called on 1st of month).

        Returns:
            True if reset successful
        """
        try:
            budget = UserAgentBudget.objects.get(user=self.user)

            budget.current_month_cost_usd = Decimal('0.00')
            budget.status = BudgetStatus.ACTIVE.value
            budget.last_reset_date = timezone.now()

            budget.save(update_fields=[
                'current_month_cost_usd',
                'status',
                'last_reset_date'
            ])

            logger.info(
                f"Monthly budget reset for user {self.user.id}. "
                f"New budget: ${budget.monthly_budget_usd}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to reset budget: {e}")
            return False

    def get_current_budget_status(self) -> Dict[str, Any]:
        """Get current budget status for user."""
        try:
            budget = UserAgentBudget.objects.get(user=self.user)

            return {
                'monthly_budget_usd': float(budget.monthly_budget_usd),
                'current_month_cost_usd': float(budget.current_month_cost_usd),
                'budget_remaining_usd': float(budget.budget_remaining_usd),
                'budget_used_percent': budget.budget_used_percent,
                'status': budget.status,
                'alert_threshold_percent': budget.alert_threshold_percent,
                'last_reset_date': budget.last_reset_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get budget status: {e}")
            return {'error': str(e)}

    def get_usage_statistics(
        self,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get API usage statistics for user.

        Args:
            days_back: Number of days to analyze

        Returns:
            Usage statistics dictionary
        """
        cutoff_date = timezone.now() - timedelta(days=days_back)

        try:
            logs = GeminiUsageLog.objects.filter(
                user=self.user,
                created_at__gte=cutoff_date
            )

            if not logs.exists():
                return {
                    'days_analyzed': days_back,
                    'total_calls': 0,
                    'total_cost_usd': 0.0,
                }

            stats = logs.aggregate(
                total_calls=Sum('total_tokens') and 1,
                total_tokens=Sum('total_tokens'),
                total_input_tokens=Sum('input_tokens'),
                total_output_tokens=Sum('output_tokens'),
                total_cost=Sum('total_cost_usd'),
            )

            call_count = logs.count()
            total_cost = float(stats['total_cost'] or Decimal('0'))

            # Routes breakdown
            route_breakdown = {}
            for route in ['auto_accept', 'agent_verify', 'agent_extract', 'human_review']:
                route_count = logs.filter(route_type=route).count()
                route_cost = logs.filter(route_type=route).aggregate(Sum('total_cost_usd'))
                route_breakdown[route] = {
                    'count': route_count,
                    'cost_usd': float(route_cost['total_cost_usd__sum'] or Decimal('0')),
                }

            return {
                'days_analyzed': days_back,
                'total_calls': call_count,
                'total_tokens': stats['total_tokens'] or 0,
                'total_input_tokens': stats['total_input_tokens'] or 0,
                'total_output_tokens': stats['total_output_tokens'] or 0,
                'total_cost_usd': total_cost,
                'average_cost_per_call': total_cost / call_count if call_count > 0 else 0.0,
                'route_breakdown': route_breakdown,
                'average_tokens_per_call': (
                    (stats['total_tokens'] or 0) / call_count
                    if call_count > 0
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get usage statistics: {e}")
            return {'error': str(e)}

    def forecast_budget(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Forecast budget usage based on recent spending trends.

        Args:
            days_ahead: Number of days to forecast

        Returns:
            Forecast data
        """
        try:
            budget = UserAgentBudget.objects.get(user=self.user)

            # Get last 14 days spending
            fourteen_days_ago = timezone.now() - timedelta(days=14)
            recent_logs = GeminiUsageLog.objects.filter(
                user=self.user,
                created_at__gte=fourteen_days_ago
            )

            if not recent_logs.exists():
                return {
                    'forecast_days': days_ahead,
                    'projected_cost_usd': 0.0,
                    'budget_sufficient': True,
                    'confidence': 'low'
                }

            recent_cost = float(
                recent_logs.aggregate(Sum('total_cost_usd'))['total_cost_usd__sum']
                or Decimal('0')
            )

            # Extrapolate to monthly
            daily_rate = recent_cost / 14
            projected_monthly = daily_rate * 30

            budget_sufficient = projected_monthly <= float(budget.monthly_budget_usd)

            return {
                'forecast_days': days_ahead,
                'daily_rate_usd': round(daily_rate, 4),
                'projected_monthly_cost_usd': round(projected_monthly, 2),
                'monthly_budget_usd': float(budget.monthly_budget_usd),
                'budget_sufficient': budget_sufficient,
                'months_of_budget': (
                    float(budget.monthly_budget_usd) / projected_monthly
                    if projected_monthly > 0
                    else 0
                ),
                'confidence': 'high' if recent_logs.count() > 50 else 'medium',
            }

        except Exception as e:
            logger.error(f"Failed to forecast budget: {e}")
            return {'error': str(e)}

    # === Helper Methods ===

    @staticmethod
    def _calculate_input_cost(tokens: int) -> Decimal:
        """Calculate input cost from tokens."""
        # Gemini-1.5-flash: $0.075 per 1M input tokens
        rate_per_token = Decimal('0.075') / Decimal('1_000_000')
        return Decimal(str(tokens)) * rate_per_token

    @staticmethod
    def _calculate_output_cost(tokens: int) -> Decimal:
        """Calculate output cost from tokens."""
        # Gemini-1.5-flash: $0.30 per 1M output tokens
        rate_per_token = Decimal('0.30') / Decimal('1_000_000')
        return Decimal(str(tokens)) * rate_per_token
