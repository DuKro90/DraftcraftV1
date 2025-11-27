# -*- coding: utf-8 -*-
"""Tests for Pattern Analysis models and admin interface."""

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


@pytest.mark.django_db
class TestExtractionFailurePattern:
    """Tests for ExtractionFailurePattern model."""

    def test_pattern_creation(self):
        """Test creating an extraction failure pattern."""
        user = User.objects.create_user(username='testuser', password='testpass')

        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Currency symbols ambiguous',
            severity='HIGH',
            confidence_threshold=Decimal('0.65'),
            affected_document_count=15,
            total_occurrences=42
        )

        assert pattern.field_name == 'amount'
        assert pattern.severity == 'HIGH'
        assert pattern.affected_document_count == 15
        assert pattern.user == user

    def test_pattern_default_values(self):
        """Test pattern default values."""
        user = User.objects.create_user(username='user2', password='testpass')

        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='vendor_name',
            pattern_type='missing_field',
            root_cause='Handwritten section'
        )

        assert pattern.severity == 'MEDIUM'
        assert pattern.is_reviewed is False
        assert pattern.is_active is True
        assert pattern.confidence_threshold == Decimal('0.70')

    def test_pattern_resolution_status_property(self):
        """Test resolution_status property."""
        user = User.objects.create_user(username='user3', password='testpass')

        # Not reviewed, no deadline
        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='test',
            pattern_type='formatting_error',
            root_cause='Test'
        )
        assert pattern.resolution_status == 'Not Started'

        # Reviewed
        pattern.is_reviewed = True
        assert pattern.resolution_status == 'Reviewed'

        # In Progress
        pattern.is_reviewed = False
        pattern.resolution_deadline = timezone.now() + timedelta(days=7)
        assert pattern.resolution_status == 'In Progress'

        # Overdue
        pattern.resolution_deadline = timezone.now() - timedelta(days=1)
        assert pattern.resolution_status == 'Overdue'

    def test_pattern_with_example_documents(self):
        """Test pattern with example documents JSON."""
        user = User.objects.create_user(username='user4', password='testpass')

        doc_ids = ['doc1', 'doc2', 'doc3']
        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test',
            example_documents=doc_ids
        )

        assert pattern.example_documents == doc_ids
        assert len(pattern.example_documents) == 3

    def test_pattern_str_representation(self):
        """Test string representation of pattern."""
        user = User.objects.create_user(username='user5', password='testpass')

        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test',
            severity='CRITICAL',
            affected_document_count=25
        )

        assert str(pattern) == 'amount - CRITICAL (25 docs)'

    def test_pattern_filtering_by_user(self):
        """Test filtering patterns by user."""
        user1 = User.objects.create_user(username='user6', password='testpass')
        user2 = User.objects.create_user(username='user7', password='testpass')

        pattern1 = ExtractionFailurePattern.objects.create(
            user=user1,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        pattern2 = ExtractionFailurePattern.objects.create(
            user=user2,
            field_name='vendor',
            pattern_type='missing_field',
            root_cause='Test'
        )

        assert ExtractionFailurePattern.objects.filter(user=user1).count() == 1
        assert ExtractionFailurePattern.objects.filter(user=user2).count() == 1
        assert pattern1.user != pattern2.user


@pytest.mark.django_db
class TestPatternReviewSession:
    """Tests for PatternReviewSession model."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='reviewer', password='testpass')
        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )

    def test_review_session_creation(self):
        """Test creating a review session."""
        admin = User.objects.create_user(username='admin', password='testpass')

        session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=admin,
            title='Review Amount Field Extraction',
            description='Analyzing low confidence scores in amount field',
            status='in_progress',
            reviewed_cases_count=10,
            approved_cases=8
        )

        assert session.title == 'Review Amount Field Extraction'
        assert session.status == 'in_progress'
        assert session.pattern == self.pattern

    def test_review_session_approval_rate(self):
        """Test approval_rate property."""
        admin = User.objects.create_user(username='admin2', password='testpass')

        session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=admin,
            title='Test',
            description='Test',
            reviewed_cases_count=20,
            approved_cases=15
        )

        assert session.approval_rate == 0.75

    def test_review_session_zero_cases(self):
        """Test approval_rate with zero cases."""
        admin = User.objects.create_user(username='admin3', password='testpass')

        session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=admin,
            title='Test',
            description='Test',
            reviewed_cases_count=0,
            approved_cases=0
        )

        assert session.approval_rate == 0.0

    def test_review_session_str_representation(self):
        """Test string representation."""
        admin = User.objects.create_user(username='admin4', password='testpass')

        session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=admin,
            title='Review Session 1',
            description='Test',
            status='draft'
        )

        assert str(session) == 'Review Session 1 - Draft - Not started'

    def test_review_session_status_choices(self):
        """Test all status choices."""
        admin = User.objects.create_user(username='admin5', password='testpass')

        statuses = ['draft', 'in_progress', 'approved', 'rejected', 'applied']

        for status in statuses:
            session = PatternReviewSession.objects.create(
                pattern=self.pattern,
                admin_user=admin,
                title=f'Test {status}',
                description='Test',
                status=status
            )
            assert session.status == status


@pytest.mark.django_db
class TestPatternFixProposal:
    """Tests for PatternFixProposal model."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='fixuser', password='testpass')
        self.admin = User.objects.create_user(username='fixadmin', password='testpass')
        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.admin,
            title='Test Session',
            description='Test'
        )

    def test_fix_proposal_creation(self):
        """Test creating a fix proposal."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Improve Currency Recognition',
            description='Add regex for German currency formats',
            fix_type='extraction_logic',
            affected_field='amount',
            confidence_score=Decimal('0.92')
        )

        assert proposal.title == 'Improve Currency Recognition'
        assert proposal.fix_type == 'extraction_logic'
        assert proposal.pattern == self.pattern

    def test_fix_proposal_default_status(self):
        """Test default status is 'proposed'."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='test'
        )

        assert proposal.status == 'proposed'

    def test_is_ready_to_deploy_property(self):
        """Test is_ready_to_deploy property."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='proposed',
            confidence_score=Decimal('0.90')
        )

        # Not ready - not validated
        assert proposal.is_ready_to_deploy is False

        # Not ready - no test rate
        proposal.status = 'validated'
        assert proposal.is_ready_to_deploy is False

        # Not ready - test rate too low
        proposal.test_success_rate = Decimal('0.80')
        assert proposal.is_ready_to_deploy is False

        # Ready
        proposal.test_success_rate = Decimal('0.90')
        proposal.confidence_score = Decimal('0.95')
        assert proposal.is_ready_to_deploy is True

    def test_fix_proposal_change_details_json(self):
        """Test storing change details as JSON."""
        changes = {
            'confidence_threshold': {
                'old': '0.70',
                'new': '0.75'
            }
        }

        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            change_details=changes
        )

        assert proposal.change_details == changes

    def test_fix_proposal_str_representation(self):
        """Test string representation."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Fix Amount Extraction',
            description='Test',
            fix_type='extraction_logic',
            affected_field='amount',
            status='testing'
        )

        assert str(proposal) == 'Fix Amount Extraction - Testing'

    def test_fix_proposal_workflow(self):
        """Test complete fix proposal workflow."""
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Test Workflow',
            description='Test',
            fix_type='field_weight',
            affected_field='amount'
        )

        # Start: proposed
        assert proposal.status == 'proposed'

        # Move to testing
        proposal.status = 'testing'
        proposal.test_sample_size = 50
        proposal.save()
        assert proposal.status == 'testing'

        # Move to validated
        proposal.status = 'validated'
        proposal.test_success_rate = Decimal('0.88')
        proposal.confidence_score = Decimal('0.85')
        proposal.save()
        assert proposal.status == 'validated'
        assert proposal.is_ready_to_deploy

        # Move to deployed
        deployer = User.objects.create_user(username='deployer', password='testpass')
        proposal.status = 'deployed'
        proposal.deployed_by = deployer
        proposal.deployed_at = timezone.now()
        proposal.save()
        assert proposal.status == 'deployed'


@pytest.mark.django_db
class TestPatternRelationships:
    """Tests for relationships between pattern models."""

    def test_review_session_cascade_delete(self):
        """Test that sessions are deleted when pattern is deleted."""
        user = User.objects.create_user(username='testuser', password='testpass')
        admin = User.objects.create_user(username='testadmin', password='testpass')

        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='test',
            pattern_type='low_confidence',
            root_cause='Test'
        )

        session = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=admin,
            title='Test',
            description='Test'
        )

        assert PatternReviewSession.objects.filter(pattern=pattern).count() == 1

        pattern.delete()
        assert PatternReviewSession.objects.filter(pattern=pattern).count() == 0

    def test_fix_proposal_cascade_delete(self):
        """Test that proposals are deleted when session is deleted."""
        user = User.objects.create_user(username='testuser2', password='testpass')
        admin = User.objects.create_user(username='testadmin2', password='testpass')

        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='test',
            pattern_type='low_confidence',
            root_cause='Test'
        )

        session = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=admin,
            title='Test',
            description='Test'
        )

        proposal = PatternFixProposal.objects.create(
            pattern=pattern,
            review_session=session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='test'
        )

        assert PatternFixProposal.objects.filter(review_session=session).count() == 1

        session.delete()
        assert PatternFixProposal.objects.filter(review_session=session).count() == 0

    def test_multiple_sessions_per_pattern(self):
        """Test multiple review sessions for same pattern."""
        user = User.objects.create_user(username='testuser3', password='testpass')
        admin1 = User.objects.create_user(username='admin1', password='testpass')
        admin2 = User.objects.create_user(username='admin2', password='testpass')

        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )

        session1 = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=admin1,
            title='First Review',
            description='Test',
            status='rejected'
        )

        session2 = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=admin2,
            title='Second Review',
            description='Test',
            status='approved'
        )

        sessions = PatternReviewSession.objects.filter(pattern=pattern)
        assert sessions.count() == 2
        assert list(sessions.values_list('title', flat=True)) == ['First Review', 'Second Review']

    def test_multiple_proposals_per_pattern(self):
        """Test multiple fix proposals for same pattern."""
        user = User.objects.create_user(username='testuser4', password='testpass')
        admin = User.objects.create_user(username='admin3', password='testpass')

        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )

        session = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=admin,
            title='Test',
            description='Test'
        )

        proposal1 = PatternFixProposal.objects.create(
            pattern=pattern,
            review_session=session,
            title='Fix Option 1',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount'
        )

        proposal2 = PatternFixProposal.objects.create(
            pattern=pattern,
            review_session=session,
            title='Fix Option 2',
            description='Test',
            fix_type='extraction_logic',
            affected_field='amount'
        )

        proposals = PatternFixProposal.objects.filter(pattern=pattern)
        assert proposals.count() == 2


@pytest.mark.django_db
class TestPatternOrdering:
    """Tests for model ordering."""

    def test_pattern_ordering_by_severity(self):
        """Test patterns are ordered by severity and doc count."""
        user = User.objects.create_user(username='orderuser', password='testpass')

        # Create patterns with different severities
        low = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='test1',
            pattern_type='low_confidence',
            root_cause='Test',
            severity='LOW',
            affected_document_count=5
        )

        critical = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='test2',
            pattern_type='low_confidence',
            root_cause='Test',
            severity='CRITICAL',
            affected_document_count=2
        )

        high = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='test3',
            pattern_type='low_confidence',
            root_cause='Test',
            severity='HIGH',
            affected_document_count=10
        )

        patterns = list(ExtractionFailurePattern.objects.all())
        assert patterns[0].severity == 'CRITICAL'
        assert patterns[1].severity == 'HIGH'
        assert patterns[2].severity == 'LOW'

    def test_session_ordering_by_creation(self):
        """Test sessions ordered by creation date (newest first)."""
        user = User.objects.create_user(username='orderuser2', password='testpass')
        admin = User.objects.create_user(username='orderadmin', password='testpass')

        pattern = ExtractionFailurePattern.objects.create(
            user=user,
            field_name='test',
            pattern_type='low_confidence',
            root_cause='Test'
        )

        session1 = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=admin,
            title='Old Session',
            description='Test'
        )

        session2 = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=admin,
            title='New Session',
            description='Test'
        )

        sessions = list(PatternReviewSession.objects.all())
        assert sessions[0].title == 'New Session'
        assert sessions[1].title == 'Old Session'
