# -*- coding: utf-8 -*-
"""Tests for SafeKnowledgeBuilder service."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from documents.pattern_models import (
    ExtractionFailurePattern,
    PatternReviewSession,
    PatternFixProposal,
)
from documents.betriebskennzahl_models import IndividuelleBetriebskennzahl
from extraction.services.knowledge_builder import (
    SafeKnowledgeBuilder,
    KnowledgeBuilderException,
)


@pytest.mark.django_db
class TestSafeKnowledgeBuilderInitialization:
    """Tests for SafeKnowledgeBuilder initialization."""

    def test_initialization_with_valid_config(self):
        """Test initializing builder with valid user configuration."""
        user = User.objects.create_user(username='builder_user', password='testpass')
        config = IndividuelleBetriebskennzahl.objects.create(user=user)

        builder = SafeKnowledgeBuilder(user)

        assert builder.user == user
        assert builder.config == config

    def test_initialization_without_config(self):
        """Test initialization fails without user configuration."""
        user = User.objects.create_user(username='no_config_user', password='testpass')

        with pytest.raises(KnowledgeBuilderException) as exc_info:
            SafeKnowledgeBuilder(user)

        assert 'has no configuration' in str(exc_info.value)

    def test_initialization_stores_user_reference(self):
        """Test that user reference is stored correctly."""
        user = User.objects.create_user(username='ref_user', password='testpass')
        IndividuelleBetriebskennzahl.objects.create(user=user)

        builder = SafeKnowledgeBuilder(user)

        assert builder.user.username == 'ref_user'


@pytest.mark.django_db
class TestCanApplyFix:
    """Tests for deployment readiness checks."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='test_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.builder = SafeKnowledgeBuilder(self.user)

        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.user,
            title='Test Session',
            description='Test'
        )

    def test_can_apply_fix_with_valid_proposal(self):
        """Test approval for fully validated fix."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        can_apply, reason = self.builder.can_apply_fix(proposal)

        assert can_apply is True
        assert 'passed' in reason

    def test_cannot_apply_proposed_fix(self):
        """Test rejection of proposed (not validated) fix."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='proposed',
            confidence_score=Decimal('0.85')
        )

        can_apply, reason = self.builder.can_apply_fix(proposal)

        assert can_apply is False
        assert 'Proposed' in reason

    def test_cannot_apply_testing_fix(self):
        """Test rejection of fix still in testing."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='testing',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        can_apply, reason = self.builder.can_apply_fix(proposal)

        assert can_apply is False
        assert 'Testing' in reason

    def test_cannot_apply_without_test_rate(self):
        """Test rejection when test rate is None."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=None,
            confidence_score=Decimal('0.85')
        )

        can_apply, reason = self.builder.can_apply_fix(proposal)

        assert can_apply is False
        assert 'not been tested' in reason

    def test_cannot_apply_with_low_test_rate(self):
        """Test rejection when test rate below 85%."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.80'),
            confidence_score=Decimal('0.85')
        )

        can_apply, reason = self.builder.can_apply_fix(proposal)

        assert can_apply is False
        assert '80.0%' in reason
        assert '85%' in reason

    def test_cannot_apply_with_low_confidence(self):
        """Test rejection when confidence below 80%."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.75')
        )

        can_apply, reason = self.builder.can_apply_fix(proposal)

        assert can_apply is False
        assert '75.0%' in reason
        assert '80%' in reason

    def test_exact_threshold_acceptance(self):
        """Test that exact thresholds are accepted."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.85'),
            confidence_score=Decimal('0.80')
        )

        can_apply, reason = self.builder.can_apply_fix(proposal)

        assert can_apply is True


@pytest.mark.django_db
class TestApplyFix:
    """Tests for applying fixes."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='apply_user', password='testpass')
        self.deployer = User.objects.create_user(username='deployer', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.builder = SafeKnowledgeBuilder(self.user)

        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test',
            is_reviewed=False
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

    def test_apply_confidence_threshold_fix(self):
        """Test applying confidence threshold adjustment."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Raise Confidence Threshold',
            description='Increase threshold for amount field',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85'),
            change_details={'confidence_threshold': {'old': '0.70', 'new': '0.75'}}
        )

        result = self.builder.apply_fix(proposal, self.deployer)

        assert result['success'] is True
        assert proposal.status == 'deployed'
        assert proposal.deployed_by == self.deployer
        assert self.pattern.is_reviewed is True
        assert 'confidence_threshold' in str(result['changes_applied'])

    def test_apply_field_weight_fix(self):
        """Test applying field weight adjustment."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Adjust Field Weight',
            description='Test',
            fix_type='field_weight',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85'),
            change_details={'old': 2.0, 'new': 2.5}
        )

        result = self.builder.apply_fix(proposal, self.deployer)

        assert result['success'] is True
        assert 'field_weight' in str(result['changes_applied'])

    def test_apply_extraction_logic_fix(self):
        """Test applying extraction logic improvement."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Improve Logic',
            description='Test',
            fix_type='extraction_logic',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85'),
            change_details={'pattern': 'new_regex'}
        )

        result = self.builder.apply_fix(proposal, self.deployer)

        assert result['success'] is True
        assert 'extraction_logic' in str(result['changes_applied'])

    def test_apply_validation_rule_fix(self):
        """Test applying new validation rule."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Add Validation',
            description='Test',
            fix_type='validation_rule',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85'),
            change_details={'rule': {'condition': 'amount > 0'}}
        )

        result = self.builder.apply_fix(proposal, self.deployer)

        assert result['success'] is True
        assert 'validation_rule' in str(result['changes_applied'])

    def test_apply_fix_fails_if_not_ready(self):
        """Test that applying non-ready fix raises exception."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='proposed',
            confidence_score=Decimal('0.85')
        )

        with pytest.raises(KnowledgeBuilderException) as exc_info:
            self.builder.apply_fix(proposal, self.deployer)

        assert 'Cannot apply fix' in str(exc_info.value)
        # Verify proposal status unchanged
        proposal.refresh_from_db()
        assert proposal.status == 'proposed'

    def test_apply_fix_updates_deployed_at(self):
        """Test that deployment timestamp is set."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        before = timezone.now()
        result = self.builder.apply_fix(proposal, self.deployer)
        after = timezone.now()

        proposal.refresh_from_db()
        assert before <= proposal.deployed_at <= after

    def test_apply_fix_marks_pattern_reviewed(self):
        """Test that pattern is marked as reviewed after deployment."""
        assert self.pattern.is_reviewed is False
        assert self.pattern.reviewed_by is None

        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        self.builder.apply_fix(proposal, self.deployer)

        self.pattern.refresh_from_db()
        assert self.pattern.is_reviewed is True
        assert self.pattern.reviewed_by == self.deployer


@pytest.mark.django_db
class TestRollbackFix:
    """Tests for rolling back deployed fixes."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='rollback_user', password='testpass')
        self.deployer = User.objects.create_user(username='deployer2', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.builder = SafeKnowledgeBuilder(self.user)

        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test',
            is_reviewed=True
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

    def test_rollback_deployed_fix(self):
        """Test rolling back a deployed fix."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='deployed',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85'),
            deployed_at=timezone.now()
        )

        result = self.builder.rollback_fix(proposal)

        assert result['success'] is True
        proposal.refresh_from_db()
        assert proposal.status == 'rolled_back'
        self.pattern.refresh_from_db()
        assert self.pattern.is_reviewed is False

    def test_cannot_rollback_non_deployed_fix(self):
        """Test that non-deployed fixes cannot be rolled back."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='proposed',
            confidence_score=Decimal('0.85')
        )

        with pytest.raises(KnowledgeBuilderException) as exc_info:
            self.builder.rollback_fix(proposal)

        assert 'Cannot rollback' in str(exc_info.value)

    def test_cannot_rollback_old_deployment(self):
        """Test that old deployments cannot be rolled back."""
        old_time = timezone.now() - timezone.timedelta(days=31)
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='deployed',
            confidence_score=Decimal('0.85'),
            deployed_at=old_time
        )

        with pytest.raises(KnowledgeBuilderException) as exc_info:
            self.builder.rollback_fix(proposal)

        assert '31 days ago' in str(exc_info.value)
        assert '30 days' in str(exc_info.value)

    def test_can_rollback_recent_deployment(self):
        """Test that recent deployments can be rolled back."""
        recent_time = timezone.now() - timezone.timedelta(days=29)
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='deployed',
            confidence_score=Decimal('0.85'),
            deployed_at=recent_time
        )

        result = self.builder.rollback_fix(proposal)

        assert result['success'] is True


@pytest.mark.django_db
class TestDeploymentHistory:
    """Tests for deployment history and querying."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='history_user', password='testpass')
        self.deployer = User.objects.create_user(username='deployer3', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.builder = SafeKnowledgeBuilder(self.user)

        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

    def test_get_ready_to_deploy_fixes(self):
        """Test getting fixes ready for deployment."""
        # Create ready fix
        ready = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Ready',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        # Create non-ready fix (test rate too low)
        not_ready = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Not Ready',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.80'),
            confidence_score=Decimal('0.85')
        )

        results = self.builder.get_ready_to_deploy_fixes()

        assert ready in results
        assert not_ready not in results
        assert results.count() == 1

    def test_get_deployed_fixes(self):
        """Test getting deployed fixes."""
        # Create deployed fix
        deployed = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Deployed',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='deployed',
            confidence_score=Decimal('0.85'),
            deployed_at=timezone.now()
        )

        # Create old deployed fix
        old_time = timezone.now() - timezone.timedelta(days=31)
        old_deployed = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Old',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='deployed',
            confidence_score=Decimal('0.85'),
            deployed_at=old_time
        )

        results = self.builder.get_deployed_fixes(days=30)

        assert deployed in results
        assert old_deployed not in results

    def test_get_rolled_back_fixes(self):
        """Test getting rolled back fixes."""
        old_time = timezone.now() - timezone.timedelta(days=15)
        rolled_back = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Rolled Back',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='rolled_back',
            confidence_score=Decimal('0.85'),
            deployed_at=old_time
        )

        results = self.builder.get_rolled_back_fixes(days=30)

        assert rolled_back in results
        assert results.count() == 1


@pytest.mark.django_db
class TestDeploymentImpact:
    """Tests for impact estimation."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='impact_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.builder = SafeKnowledgeBuilder(self.user)

        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test',
            affected_document_count=100
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

    def test_impact_estimation(self):
        """Test impact estimation for fix."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            test_success_rate=Decimal('0.80')
        )

        impact = self.builder.get_deployment_impact(proposal)

        assert impact['field'] == 'amount'
        assert impact['affected_documents'] == 100
        assert impact['estimated_improvement'] == 80
        assert impact['improvement_percentage'] == 80.0

    def test_impact_with_zero_affected_documents(self):
        """Test impact calculation with zero affected documents."""
        pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='test',
            pattern_type='low_confidence',
            root_cause='Test',
            affected_document_count=0
        )
        proposal = PatternFixProposal.objects.create(
            pattern=pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='test',
            test_success_rate=Decimal('0.90')
        )

        impact = self.builder.get_deployment_impact(proposal)

        assert impact['improvement_percentage'] == 0.0


@pytest.mark.django_db
class TestDeploymentSummary:
    """Tests for deployment summary."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='summary_user', password='testpass')
        self.deployer = User.objects.create_user(username='deployer4', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.builder = SafeKnowledgeBuilder(self.user)

        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

    def test_deployment_summary(self):
        """Test deployment summary metrics."""
        # Create ready fix
        PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Ready',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        # Create deployed fix
        PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Deployed',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='deployed',
            confidence_score=Decimal('0.85'),
            deployed_at=timezone.now()
        )

        summary = self.builder.get_deployment_summary()

        assert summary['ready_to_deploy'] == 1
        assert summary['deployed_this_month'] == 1
        assert summary['total_fixes_in_progress'] >= 1


@pytest.mark.django_db
class TestDeploymentChecklist:
    """Tests for deployment checklist."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='checklist_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.builder = SafeKnowledgeBuilder(self.user)

        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

    def test_checklist_all_passed(self):
        """Test checklist for fully validated fix."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85'),
            test_sample_size=50,
            validation_notes='All tests passed'
        )

        checklist = self.builder.create_deployment_checklist(proposal)

        assert all(item['passed'] for item in checklist if item['required'])

    def test_checklist_fails_on_low_test_rate(self):
        """Test checklist failure on low test rate."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.80'),
            confidence_score=Decimal('0.85')
        )

        checklist = self.builder.create_deployment_checklist(proposal)

        test_rate_check = [c for c in checklist if 'Test Success Rate' in c['name']][0]
        assert test_rate_check['passed'] is False

    def test_checklist_contains_all_checks(self):
        """Test that checklist contains all required checks."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='proposed'
        )

        checklist = self.builder.create_deployment_checklist(proposal)

        check_names = [c['name'] for c in checklist]
        assert 'Status is Validated' in check_names
        assert 'Test Success Rate >= 85%' in check_names
        assert 'Confidence Score >= 80%' in check_names
        assert 'Test Cases Executed' in check_names


@pytest.mark.django_db
class TestKnowledgeBuilderEdgeCases:
    """Tests for edge cases and error handling."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='edge_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.builder = SafeKnowledgeBuilder(self.user)

    def test_multiple_patterns_independent(self):
        """Test that fixes for different patterns are independent."""
        pattern1 = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test',
            is_reviewed=False
        )
        pattern2 = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='vendor',
            pattern_type='missing_field',
            root_cause='Test',
            is_reviewed=False
        )

        session1 = PatternReviewSession.objects.create(
            pattern=pattern1,
            admin_user=self.user,
            title='Test',
            description='Test'
        )
        session2 = PatternReviewSession.objects.create(
            pattern=pattern2,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

        proposal1 = PatternFixProposal.objects.create(
            pattern=pattern1,
            review_session=session1,
            title='Fix 1',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        proposal2 = PatternFixProposal.objects.create(
            pattern=pattern2,
            review_session=session2,
            title='Fix 2',
            description='Test',
            fix_type='field_weight',
            affected_field='vendor',
            status='proposed'
        )

        ready = self.builder.get_ready_to_deploy_fixes()

        assert proposal1 in ready
        assert proposal2 not in ready

    def test_deployment_ordering_by_severity(self):
        """Test that ready fixes are ordered by pattern severity."""
        pattern_low = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='low',
            pattern_type='low_confidence',
            root_cause='Test',
            severity='LOW'
        )
        pattern_crit = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='critical',
            pattern_type='low_confidence',
            root_cause='Test',
            severity='CRITICAL'
        )

        session = PatternReviewSession.objects.create(
            pattern=pattern_low,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

        fix_low = PatternFixProposal.objects.create(
            pattern=pattern_low,
            review_session=session,
            title='Low',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='low',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        session2 = PatternReviewSession.objects.create(
            pattern=pattern_crit,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

        fix_crit = PatternFixProposal.objects.create(
            pattern=pattern_crit,
            review_session=session2,
            title='Critical',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='critical',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        ready = list(self.builder.get_ready_to_deploy_fixes())

        # Critical should come first
        assert ready.index(fix_crit) < ready.index(fix_low)
