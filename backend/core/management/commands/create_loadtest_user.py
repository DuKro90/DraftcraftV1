"""
Django management command to create/retrieve load test user with authentication token.

Usage:
    python manage.py create_loadtest_user

Output:
    Displays load test credentials (username and token) for use in load tests.
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

try:
    from rest_framework.authtoken.models import Token
except ImportError:
    # Fallback if rest_framework not installed
    Token = None


User = get_user_model()


class Command(BaseCommand):
    help = "Create or retrieve a load test user and display authentication token"

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='loadtest_user',
            help='Username for the load test user (default: loadtest_user)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Password for the load test user (auto-generated if not provided)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset token for existing user',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options.get('password')
        reset_token = options.get('reset', False)

        # Generate password if not provided
        if not password:
            password = f"LoadTest{os.urandom(8).hex().upper()}!Secure"

        try:
            # Try to get existing user
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(f"Found existing user: {username}")
            )

            # Reset token if requested
            if reset_token:
                Token.objects.filter(user=user).delete()
                self.stdout.write(
                    self.style.WARNING("Deleted existing token")
                )
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=username,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created new user: {username}")
            )

        # Get or create token
        if Token is None:
            raise CommandError(
                "rest_framework.authtoken not available. "
                "Ensure djangorestframework is installed."
            )

        token, created = Token.objects.get_or_create(user=user)

        # Display credentials
        self.stdout.write(
            self.style.SUCCESS("\n" + "=" * 70)
        )
        self.stdout.write(
            self.style.SUCCESS("LOAD TEST USER CREDENTIALS")
        )
        self.stdout.write(
            self.style.SUCCESS("=" * 70)
        )
        self.stdout.write(
            self.style.HTTP_INFO(f"Username: {username}")
        )
        self.stdout.write(
            self.style.HTTP_INFO(f"Password: {password}")
        )
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Token: {token.key}")
        )
        self.stdout.write(
            self.style.SUCCESS("=" * 70 + "\n")
        )

        self.stdout.write(
            self.style.WARNING(
                "IMPORTANT: Save these credentials for load testing.\n"
                "Use the token in HTTP Authorization header:\n"
                "Authorization: Token <token_key>"
            )
        )
