"""
Setup script for load testing data.

Creates necessary test data for load testing:
- Load test user (with token)
- Sample documents
- Sample proposals

Usage:
    python tests/fixtures/setup_loadtest_data.py

Run this before executing load tests to ensure test data exists.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from documents.models import Document, Proposal


User = get_user_model()


def create_load_test_user() -> str:
    """
    Create or retrieve the load test user and return the authentication token.

    Returns:
        Authentication token string
    """
    username = "loadtest_user"
    password = "LoadTest2024!Secure"

    # Get or create user
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": "loadtest@example.com", "is_active": True},
    )

    if created:
        user.set_password(password)
        user.save()
        print(f"Created new load test user: {username}")
    else:
        print(f"Using existing load test user: {username}")

    # Get or create token
    token, token_created = Token.objects.get_or_create(user=user)

    if token_created:
        print(f"Created new token for user: {username}")
    else:
        print(f"Using existing token for user: {username}")

    return token.key


def create_sample_documents() -> list:
    """
    Create sample documents for load testing.

    Returns:
        List of created document IDs
    """
    # Get or create load test user
    try:
        user = User.objects.get(username="loadtest_user")
    except User.DoesNotExist:
        print("Load test user not found. Creating...")
        user = User.objects.create_user(
            username="loadtest_user",
            password="LoadTest2024!Secure",
        )

    # Sample documents
    sample_docs = [
        {
            "title": "Angebot Schreinerei 001",
            "description": "Schreinerarbeiten für Wohnzimmer",
            "source": "uploaded",
        },
        {
            "title": "Angebot Polsterei 001",
            "description": "Polsterarbeiten für Sofa und Sessel",
            "source": "uploaded",
        },
        {
            "title": "Rechnung Holzlieferant",
            "description": "Holzlieferung für Projekte",
            "source": "uploaded",
        },
        {
            "title": "Angebot Metallbau",
            "description": "Stahlkonstruktion und Metallbearbeitung",
            "source": "uploaded",
        },
        {
            "title": "Abrechnungsunterlagen",
            "description": "Verschiedene Abrechnungsdokumente",
            "source": "uploaded",
        },
    ]

    created_ids = []
    for doc_data in sample_docs:
        doc, created = Document.objects.get_or_create(
            title=doc_data["title"],
            user=user,
            defaults={
                "description": doc_data["description"],
                "source": doc_data["source"],
                "status": "uploaded",
            },
        )
        if created:
            print(f"Created sample document: {doc_data['title']}")
            created_ids.append(doc.id)
        else:
            print(f"Using existing document: {doc_data['title']}")
            created_ids.append(doc.id)

    return created_ids


def create_sample_proposals() -> list:
    """
    Create sample proposals for load testing.

    Returns:
        List of created proposal IDs
    """
    # Get or create load test user
    try:
        user = User.objects.get(username="loadtest_user")
    except User.DoesNotExist:
        print("Load test user not found. Creating...")
        user = User.objects.create_user(
            username="loadtest_user",
            password="LoadTest2024!Secure",
        )

    # Sample proposals
    sample_proposals = [
        {
            "title": "Schreinerarbeiten Wohnzimmer",
            "description": "Hochwertige Einbauschränke und Regale",
            "status": "pending",
        },
        {
            "title": "Polsterarbeiten Möbel",
            "description": "Aufarbeitung alter Möbelstücke",
            "status": "pending",
        },
        {
            "title": "Metallkonstruktion Treppe",
            "description": "Stahltreppe mit Handlauf",
            "status": "accepted",
        },
    ]

    created_ids = []
    for prop_data in sample_proposals:
        prop, created = Proposal.objects.get_or_create(
            title=prop_data["title"],
            user=user,
            defaults={
                "description": prop_data["description"],
                "status": prop_data["status"],
            },
        )
        if created:
            print(f"Created sample proposal: {prop_data['title']}")
            created_ids.append(prop.id)
        else:
            print(f"Using existing proposal: {prop_data['title']}")
            created_ids.append(prop.id)

    return created_ids


def main():
    """Run all setup tasks."""
    print("\n" + "=" * 70)
    print("LOAD TEST DATA SETUP")
    print("=" * 70 + "\n")

    # Create load test user and get token
    print("Step 1: Setting up load test user...")
    token = create_load_test_user()

    # Create sample documents
    print("\nStep 2: Creating sample documents...")
    doc_ids = create_sample_documents()

    # Create sample proposals
    print("\nStep 3: Creating sample proposals...")
    prop_ids = create_sample_proposals()

    # Print summary
    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    print(f"\nLoadtest User: loadtest_user")
    print(f"Authentication Token: {token}")
    print(f"Sample Documents Created: {len(doc_ids)}")
    print(f"Sample Proposals Created: {len(prop_ids)}")
    print("\nUse the token above in HTTP Authorization header:")
    print("Authorization: Token <token_key>")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
