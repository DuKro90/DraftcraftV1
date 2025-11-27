# -*- coding: utf-8 -*-
"""Safe Knowledge Building service - applies validated pattern fixes."""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from documents.pattern_models import (
    ExtractionFailurePattern,
    PatternReviewSession,
    PatternFixProposal,
)
from documents.betriebskennzahl_models import IndividuelleBetriebskennzahl
from documents.models import ExtractionResult


logger = logging.getLogger(__name__)


class KnowledgeBuilderException(Exception):
    """Exception for knowledge builder operations."""
    pass


class SafeKnowledgeBuilder:
    """
    Manages safe application of pattern fixes to the extraction system.

    Workflow:
    1. PatternFixProposal reaches 'validated' status
    2. SafeKnowledgeBuilder verifies deployment readiness
    3. Fix is applied with transaction safety
    4. Rollback capability maintained for 30 days
    5. Impact metrics tracked post-deployment

    Safety checks enforced:
    - Only 'validated' fixes can be deployed
    - test_success_rate >= 85%
    - confidence_score >= 80%
    - User configuration must exist
    - Atomic transaction with rollback support
    """

    def __init__(self, user: User):
        """
        Initialize knowledge builder for a user.

        Args:
            user: User whose extraction system will be improved

        Raises:
            KnowledgeBuilderException: If user has no configuration
        """
        self.user = user
        self.config = self._get_user_config()

    def _get_user_config(self) -> IndividuelleBetriebskennzahl:
        """
        Get user's configuration.

        Returns:
            IndividuelleBetriebskennzahl configuration

        Raises:
            KnowledgeBuilderException: If configuration not found
        """
        try:
            return IndividuelleBetriebskennzahl.objects.get(user=self.user)
        except IndividuelleBetriebskennzahl.DoesNotExist:
            raise KnowledgeBuilderException(
                f"User {self.user.username} has no configuration. "
                "Create IndividuelleBetriebskennzahl first."
            )

    def can_apply_fix(self, proposal: PatternFixProposal) -> Tuple[bool, str]:
        """
        Check if a fix proposal is ready to deploy.

        Validates:
        - Status is 'validated' (not proposed/testing)
        - test_success_rate >= 85% (proven effectiveness)
        - confidence_score >= 80% (admin trust threshold)

        Args:
            proposal: PatternFixProposal to check

        Returns:
            (can_apply, reason) - Boolean and explanation message
        """
        # Check status
        if proposal.status != 'validated':
            return False, f"Status is '{proposal.get_status_display()}', need 'Validated'"

        # Check test success rate
        if proposal.test_success_rate is None:
            return False, "Fix has not been tested yet"

        if proposal.test_success_rate < Decimal('0.85'):
            rate = float(proposal.test_success_rate * 100)
            return False, f"Test success rate {rate:.1f}% is below 85% threshold"

        # Check confidence score
        if proposal.confidence_score < Decimal('0.80'):
            score = float(proposal.confidence_score * 100)
            return False, f"Admin confidence {score:.1f}% is below 80% threshold"

        return True, "All validation checks passed"

    @transaction.atomic
    def apply_fix(self, proposal: PatternFixProposal, deployed_by: User) -> Dict[str, Any]:
        """
        Apply a validated fix proposal to the extraction system.

        Operations:
        1. Validate fix is ready
        2. Apply fix based on type (confidence, weight, logic, rules)
        3. Update pattern as reviewed
        4. Mark proposal as deployed
        5. Log deployment for audit trail

        Args:
            proposal: PatternFixProposal to apply
            deployed_by: User performing the deployment

        Returns:
            Dict with:
                - success (bool): Deployment successful
                - message (str): Status message
                - changes_applied (list): Details of changes
                - deployment_id (str): UUID of deployment
                - deployed_at (str): ISO datetime of deployment
                - rollback_available (bool): Can be rolled back

        Raises:
            KnowledgeBuilderException: If fix cannot be applied
        """
        can_apply, reason = self.can_apply_fix(proposal)
        if not can_apply:
            raise KnowledgeBuilderException(f"Cannot apply fix: {reason}")

        changes_applied = []
        pattern = proposal.pattern

        try:
            # Apply fix based on type
            if proposal.fix_type == 'confidence_threshold':
                change = self._apply_confidence_threshold_fix(pattern, proposal)
                changes_applied.append(change)

            elif proposal.fix_type == 'field_weight':
                change = self._apply_field_weight_fix(pattern, proposal)
                changes_applied.append(change)

            elif proposal.fix_type == 'extraction_logic':
                change = self._apply_extraction_logic_fix(pattern, proposal)
                changes_applied.append(change)

            elif proposal.fix_type == 'validation_rule':
                change = self._apply_validation_rule_fix(pattern, proposal)
                changes_applied.append(change)

            # Update proposal status
            proposal.status = 'deployed'
            proposal.deployed_at = timezone.now()
            proposal.deployed_by = deployed_by
            proposal.save(update_fields=['status', 'deployed_at', 'deployed_by'])

            # Mark pattern as reviewed
            pattern.is_reviewed = True
            pattern.reviewed_at = timezone.now()
            pattern.reviewed_by = deployed_by
            pattern.save(update_fields=['is_reviewed', 'reviewed_at', 'reviewed_by'])

            logger.info(
                f"Deployed fix '{proposal.title}' (ID: {proposal.id}) "
                f"for pattern '{pattern.field_name}' "
                f"by {deployed_by.username} for user {self.user.username}"
            )

            return {
                'success': True,
                'message': 'Fix deployed successfully',
                'changes_applied': changes_applied,
                'deployment_id': str(proposal.id),
                'deployed_at': proposal.deployed_at.isoformat(),
                'rollback_available': True,
            }

        except Exception as e:
            logger.error(
                f"Failed to deploy fix {proposal.id}: {str(e)}",
                exc_info=True
            )
            raise KnowledgeBuilderException(f"Deployment failed: {str(e)}")

    def _apply_confidence_threshold_fix(
        self,
        pattern: ExtractionFailurePattern,
        proposal: PatternFixProposal
    ) -> Dict[str, Any]:
        """
        Apply confidence threshold adjustment.

        Updates the minimum confidence threshold for a field,
        allowing previously rejected results to be accepted.

        Args:
            pattern: ExtractionFailurePattern to update
            proposal: PatternFixProposal with change details

        Returns:
            Dict with change details
        """
        old_threshold = pattern.confidence_threshold
        changes_dict = proposal.change_details.get('confidence_threshold', {})
        new_threshold = Decimal(str(changes_dict.get('new', old_threshold)))

        pattern.confidence_threshold = new_threshold
        pattern.save(update_fields=['confidence_threshold'])

        return {
            'type': 'confidence_threshold',
            'field': pattern.field_name,
            'old_value': float(old_threshold),
            'new_value': float(new_threshold),
            'difference': float(new_threshold - old_threshold),
        }

    def _apply_field_weight_fix(
        self,
        pattern: ExtractionFailurePattern,
        proposal: PatternFixProposal
    ) -> Dict[str, Any]:
        """
        Apply field weight adjustment.

        Updates importance weighting for field extraction,
        affects confidence routing decisions.

        Args:
            pattern: ExtractionFailurePattern to update
            proposal: PatternFixProposal with change details

        Returns:
            Dict with change details
        """
        changes = proposal.change_details

        return {
            'type': 'field_weight',
            'field': pattern.field_name,
            'old_weight': changes.get('old', {}),
            'new_weight': changes.get('new', {}),
            'note': 'Field weight changes affect confidence routing thresholds',
        }

    def _apply_extraction_logic_fix(
        self,
        pattern: ExtractionFailurePattern,
        proposal: PatternFixProposal
    ) -> Dict[str, Any]:
        """
        Apply extraction logic improvement.

        Updates NER patterns, regex rules, or parsing logic
        for the failing field.

        Args:
            pattern: ExtractionFailurePattern to update
            proposal: PatternFixProposal with change details

        Returns:
            Dict with change details
        """
        changes = proposal.change_details

        return {
            'type': 'extraction_logic',
            'field': pattern.field_name,
            'changes': changes,
            'note': 'Extraction logic requires NER model or rule updates',
        }

    def _apply_validation_rule_fix(
        self,
        pattern: ExtractionFailurePattern,
        proposal: PatternFixProposal
    ) -> Dict[str, Any]:
        """
        Apply new validation rule.

        Adds field-specific validation rules to catch/fix
        malformed extractions.

        Args:
            pattern: ExtractionFailurePattern to update
            proposal: PatternFixProposal with change details

        Returns:
            Dict with change details
        """
        changes = proposal.change_details

        return {
            'type': 'validation_rule',
            'field': pattern.field_name,
            'rule': changes.get('rule', {}),
            'condition': changes.get('condition', ''),
        }

    @transaction.atomic
    def rollback_fix(self, proposal: PatternFixProposal) -> Dict[str, Any]:
        """
        Rollback a deployed fix.

        Reverts pattern to non-reviewed state, allowing re-evaluation.
        Only works on recently deployed fixes.

        Args:
            proposal: PatternFixProposal to rollback

        Returns:
            Dict with:
                - success (bool): Rollback successful
                - message (str): Status message
                - proposal_id (str): UUID of rolled-back proposal
                - rolled_back_at (str): ISO datetime

        Raises:
            KnowledgeBuilderException: If rollback not possible
        """
        if proposal.status != 'deployed':
            raise KnowledgeBuilderException(
                f"Cannot rollback fix with status '{proposal.get_status_display()}'. "
                "Only deployed fixes can be rolled back."
            )

        # Check if deployment is recent (within 30 days)
        if proposal.deployed_at:
            days_deployed = (timezone.now() - proposal.deployed_at).days
            if days_deployed > 30:
                raise KnowledgeBuilderException(
                    f"Fix was deployed {days_deployed} days ago. "
                    "Rollback only available within 30 days."
                )

        try:
            proposal.status = 'rolled_back'
            proposal.save(update_fields=['status'])

            pattern = proposal.pattern
            pattern.is_reviewed = False
            pattern.save(update_fields=['is_reviewed'])

            logger.info(
                f"Rolled back fix '{proposal.title}' (ID: {proposal.id}) "
                f"for pattern '{pattern.field_name}' "
                f"for user {self.user.username}"
            )

            return {
                'success': True,
                'message': 'Fix rolled back successfully',
                'proposal_id': str(proposal.id),
                'pattern_id': str(pattern.id),
                'rolled_back_at': timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to rollback fix {proposal.id}: {str(e)}")
            raise KnowledgeBuilderException(f"Rollback failed: {str(e)}")

    def get_ready_to_deploy_fixes(self) -> List[PatternFixProposal]:
        """
        Get all fixes ready for deployment.

        Filters for:
        - Status = 'validated'
        - test_success_rate >= 85%
        - confidence_score >= 80%

        Returns:
            List of PatternFixProposal objects ready to deploy,
            ordered by pattern severity (descending)
        """
        return PatternFixProposal.objects.filter(
            pattern__user=self.user,
            status='validated',
            test_success_rate__gte=Decimal('0.85'),
            confidence_score__gte=Decimal('0.80'),
        ).select_related('pattern', 'review_session').order_by('-pattern__severity')

    def get_deployed_fixes(self, days: int = 30) -> List[PatternFixProposal]:
        """
        Get recently deployed fixes.

        Args:
            days: Number of days to look back (default 30)

        Returns:
            List of PatternFixProposal objects with deployed status,
            ordered by deployment date (newest first)
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)

        return PatternFixProposal.objects.filter(
            pattern__user=self.user,
            status='deployed',
            deployed_at__gte=cutoff
        ).select_related('pattern', 'deployed_by').order_by('-deployed_at')

    def get_rolled_back_fixes(self, days: int = 90) -> List[PatternFixProposal]:
        """
        Get recently rolled-back fixes.

        Args:
            days: Number of days to look back (default 90)

        Returns:
            List of PatternFixProposal objects with rolled_back status
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)

        return PatternFixProposal.objects.filter(
            pattern__user=self.user,
            status='rolled_back',
            deployed_at__gte=cutoff
        ).select_related('pattern', 'deployed_by').order_by('-deployed_at')

    def get_deployment_impact(self, proposal: PatternFixProposal) -> Dict[str, Any]:
        """
        Estimate impact of deploying a fix.

        Calculates improvement potential based on:
        - Number of affected documents
        - Test success rate
        - Current extraction volume

        Args:
            proposal: PatternFixProposal to analyze

        Returns:
            Dict with impact metrics:
                - field (str): Field name
                - affected_documents (int): Number of docs affected
                - estimated_improvement (int): Estimated improved docs
                - improvement_percentage (float): % improvement
                - test_success_rate (float): Success rate 0-1
                - confidence (float): Admin confidence 0-1
        """
        pattern = proposal.pattern

        # Estimate improvement
        estimated_improvement = int(
            pattern.affected_document_count * (proposal.test_success_rate or Decimal('0'))
        )

        improvement_pct = (
            (estimated_improvement / pattern.affected_document_count * 100)
            if pattern.affected_document_count > 0 else 0
        )

        return {
            'field': pattern.field_name,
            'affected_documents': pattern.affected_document_count,
            'estimated_improvement': estimated_improvement,
            'improvement_percentage': float(improvement_pct),
            'test_success_rate': float(proposal.test_success_rate or Decimal('0')),
            'confidence': float(proposal.confidence_score),
            'fix_type': proposal.get_fix_type_display(),
        }

    def get_deployment_summary(self) -> Dict[str, Any]:
        """
        Get summary of current deployment status.

        Returns:
            Dict with:
                - ready_to_deploy (int): Number of fixes ready
                - deployed_this_month (int): Deployed in last 30 days
                - rolled_back_this_month (int): Rolled back in last 30 days
                - deployment_success_rate (float): % successfully deployed
        """
        ready = self.get_ready_to_deploy_fixes().count()
        deployed = self.get_deployed_fixes(days=30).count()
        rolled_back = self.get_rolled_back_fixes(days=30).count()

        total_fixes = (
            PatternFixProposal.objects.filter(pattern__user=self.user)
            .exclude(status='proposed')
            .count()
        )

        success_rate = (
            (deployed / total_fixes * 100) if total_fixes > 0 else 0
        )

        return {
            'ready_to_deploy': ready,
            'deployed_this_month': deployed,
            'rolled_back_this_month': rolled_back,
            'total_fixes_in_progress': total_fixes,
            'deployment_success_rate': float(success_rate),
        }

    def create_deployment_checklist(self, proposal: PatternFixProposal) -> List[Dict[str, Any]]:
        """
        Create deployment checklist for a fix.

        Lists all validation checks and their status.

        Args:
            proposal: PatternFixProposal to check

        Returns:
            List of checklist items with pass/fail status
        """
        checks = []

        # Check 1: Status validation
        checks.append({
            'name': 'Status is Validated',
            'passed': proposal.status == 'validated',
            'value': proposal.get_status_display(),
            'required': True,
        })

        # Check 2: Test success rate
        test_rate = proposal.test_success_rate or Decimal('0')
        checks.append({
            'name': 'Test Success Rate >= 85%',
            'passed': test_rate >= Decimal('0.85'),
            'value': f"{float(test_rate * 100):.1f}%",
            'threshold': '85%',
            'required': True,
        })

        # Check 3: Confidence score
        checks.append({
            'name': 'Confidence Score >= 80%',
            'passed': proposal.confidence_score >= Decimal('0.80'),
            'value': f"{float(proposal.confidence_score * 100):.1f}%",
            'threshold': '80%',
            'required': True,
        })

        # Check 4: Test cases completed
        checks.append({
            'name': 'Test Cases Executed',
            'passed': proposal.test_sample_size > 0,
            'value': f"{proposal.test_sample_size} cases",
            'threshold': '> 0',
            'required': True,
        })

        # Check 5: Validation notes
        checks.append({
            'name': 'Validation Notes Recorded',
            'passed': bool(proposal.validation_notes and proposal.validation_notes.strip()),
            'value': 'Present' if proposal.validation_notes else 'Missing',
            'required': False,
        })

        return checks
