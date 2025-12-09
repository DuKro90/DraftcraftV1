"""Management command to sync wiki articles from markdown files.

Usage:
    python manage.py sync_wiki                    # Sync all articles
    python manage.py sync_wiki --create-initial   # Create initial articles from docs
    python manage.py sync_wiki --article 123      # Sync specific article
"""

import os
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from documents.models_wiki import WikiCategory, WikiArticle


def parse_markdown_frontmatter(content):
    """
    Parse YAML frontmatter from markdown file.

    Example:
        ---
        title: Bulk Upload Guide
        category: data-import
        difficulty: beginner
        keywords: upload, excel, csv, import
        ---
        # Content here...
    """
    if not content.startswith('---'):
        return {}, content

    try:
        # Split on second ---
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        frontmatter_text = parts[1].strip()
        markdown_content = parts[2].strip()

        # Parse simple YAML-like format
        metadata = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

        return metadata, markdown_content

    except Exception:
        return {}, content


def sync_article(article):
    """Sync a single article from its source file."""
    if not article.source_file:
        raise ValueError(f"Article '{article.title}' has no source file configured")

    filepath = Path(article.source_file)
    if not filepath.exists():
        raise FileNotFoundError(f"Source file not found: {filepath}")

    # Read markdown file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter if present
    metadata, markdown_content = parse_markdown_frontmatter(content)

    # Update article
    if metadata.get('title'):
        article.title = metadata['title']

    if metadata.get('summary'):
        article.summary = metadata['summary']

    if metadata.get('difficulty'):
        article.difficulty = metadata['difficulty']

    if metadata.get('keywords'):
        article.keywords = metadata['keywords']

    if metadata.get('estimated_time'):
        article.estimated_time = metadata['estimated_time']

    # Update content
    article.content = markdown_content
    article.last_synced_at = timezone.now()
    article.save()

    return article


class Command(BaseCommand):
    help = 'Sync wiki articles from markdown documentation files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-initial',
            action='store_true',
            help='Create initial wiki articles from existing docs'
        )
        parser.add_argument(
            '--article',
            type=int,
            help='Sync specific article by ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing'
        )

    def handle(self, *args, **options):
        if options['create_initial']:
            self.create_initial_articles()
        elif options['article']:
            self.sync_single_article(options['article'], options['dry_run'])
        else:
            self.sync_all_articles(options['dry_run'])

    def create_initial_articles(self):
        """Create initial wiki articles from existing documentation."""
        self.stdout.write(self.style.SUCCESS('Creating initial wiki articles...'))

        # Get or create categories
        categories = {
            'getting-started': self.get_or_create_category(
                'Getting Started',
                '🚀',
                'Essential guides for new users',
                order=1
            ),
            'data-import': self.get_or_create_category(
                'Data Import & Export',
                '📤',
                'Guides for importing and exporting data',
                order=2
            ),
            'configuration': self.get_or_create_category(
                'Configuration',
                '⚙️',
                'System configuration and setup',
                order=3
            ),
            'troubleshooting': self.get_or_create_category(
                'Troubleshooting',
                '🐛',
                'Common problems and solutions',
                order=4
            ),
            'advanced': self.get_or_create_category(
                'Advanced Features',
                '🔧',
                'Advanced functionality and customization',
                order=5
            ),
        }

        # Define initial articles to create
        articles_to_create = [
            {
                'title': 'Bulk Upload: Getting Started',
                'slug': 'bulk-upload-getting-started',
                'category': categories['data-import'],
                'difficulty': 'beginner',
                'source_file': 'C:\\Codes\\DraftcraftV1\\backend\\BULK_UPLOAD_GUIDE.md',
                'summary': 'Learn how to upload wood types, materials, and pricing data from Excel/CSV files in minutes instead of hours.',
                'keywords': 'bulk upload, excel, csv, import, wood types, materials, betriebskennzahlen',
                'estimated_time': '10 minutes',
                'is_featured': True,
            },
            {
                'title': 'Understanding Admin Tooltips',
                'slug': 'admin-tooltips-guide',
                'category': categories['getting-started'],
                'difficulty': 'beginner',
                'source_file': 'C:\\Codes\\DraftcraftV1\\backend\\ADMIN_TOOLTIPS_GUIDE.md',
                'summary': 'Complete guide to understanding the helpful tooltips and color-coded help text in the Django admin interface.',
                'keywords': 'admin, tooltips, help text, interface, guide',
                'estimated_time': '5 minutes',
                'is_featured': False,
            },
            {
                'title': 'Docker Build & Deployment',
                'slug': 'docker-build-deployment',
                'category': categories['configuration'],
                'difficulty': 'advanced',
                'source_file': 'C:\\Codes\\DraftcraftV1\\.claude\\claude code docker build guide.md',
                'summary': 'Complete guide to building and deploying the application with Docker, including troubleshooting common issues.',
                'keywords': 'docker, deployment, build, cloud run, gcp',
                'estimated_time': '20 minutes',
                'is_featured': False,
            },
            {
                'title': 'Phase 3: Betriebskennzahlen System',
                'slug': 'phase3-betriebskennzahlen',
                'category': categories['advanced'],
                'difficulty': 'intermediate',
                'source_file': 'C:\\Codes\\DraftcraftV1\\docs\\phases\\phase3_integration_summary.md',
                'summary': 'Understanding the 8-step pricing calculation engine with TIER 1/2/3 configuration.',
                'keywords': 'betriebskennzahlen, pricing, calculation, tier, phase 3',
                'estimated_time': '15 minutes',
                'is_featured': False,
            },
            {
                'title': 'Supabase Migration Guide',
                'slug': 'supabase-migration',
                'category': categories['configuration'],
                'difficulty': 'advanced',
                'source_file': 'C:\\Codes\\DraftcraftV1\\.claude\\guides\\supabase-migration-guide.md',
                'summary': 'Step-by-step guide to migrating from local PostgreSQL to Supabase with RLS security.',
                'keywords': 'supabase, migration, database, postgresql, rls',
                'estimated_time': '30-45 minutes',
                'is_featured': False,
            },
        ]

        created_count = 0
        skipped_count = 0

        for article_data in articles_to_create:
            # Check if article already exists
            if WikiArticle.objects.filter(slug=article_data['slug']).exists():
                self.stdout.write(
                    self.style.WARNING(f"  Skipped: {article_data['title']} (already exists)")
                )
                skipped_count += 1
                continue

            # Check if source file exists
            source_file = Path(article_data['source_file'])
            if not source_file.exists():
                self.stdout.write(
                    self.style.ERROR(f"  Error: Source file not found for {article_data['title']}")
                )
                continue

            # Read content
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter
            metadata, markdown_content = parse_markdown_frontmatter(content)

            # Create article
            article = WikiArticle.objects.create(
                title=metadata.get('title', article_data['title']),
                slug=article_data['slug'],
                category=article_data['category'],
                difficulty=article_data['difficulty'],
                summary=metadata.get('summary', article_data['summary']),
                content=markdown_content,
                source_file=str(source_file),
                keywords=metadata.get('keywords', article_data['keywords']),
                estimated_time=metadata.get('estimated_time', article_data['estimated_time']),
                is_published=True,
                is_featured=article_data['is_featured'],
                last_synced_at=timezone.now(),
            )

            try:
                self.stdout.write(
                    self.style.SUCCESS(f"  Created: {article.title}")
                )
            except UnicodeEncodeError:
                self.stdout.write(
                    self.style.SUCCESS(f"  [OK] Created: {article.title}")
                )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'\nCreated {created_count} articles, skipped {skipped_count}')
        )

    def sync_single_article(self, article_id, dry_run=False):
        """Sync a single article by ID."""
        try:
            article = WikiArticle.objects.get(pk=article_id)
        except WikiArticle.DoesNotExist:
            raise CommandError(f'Article with ID {article_id} does not exist')

        if not article.source_file:
            raise CommandError(f'Article "{article.title}" has no source file configured')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Would sync: {article.title}')
            )
            self.stdout.write(f'  Source: {article.source_file}')
            return

        try:
            sync_article(article)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Synced: {article.title}')
            )
        except Exception as e:
            raise CommandError(f'Failed to sync article: {str(e)}')

    def sync_all_articles(self, dry_run=False):
        """Sync all articles that have source files."""
        articles = WikiArticle.objects.filter(source_file__isnull=False).exclude(source_file='')

        if not articles.exists():
            self.stdout.write(
                self.style.WARNING('No articles with source files found')
            )
            return

        synced_count = 0
        error_count = 0

        self.stdout.write(f'Found {articles.count()} articles to sync...\n')

        for article in articles:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'[DRY RUN] Would sync: {article.title}')
                )
                self.stdout.write(f'  Source: {article.source_file}')
                continue

            try:
                sync_article(article)
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Synced: {article.title}')
                )
                synced_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error syncing {article.title}: {str(e)}')
                )
                error_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\n[DRY RUN] Would sync {articles.count()} articles')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nSynced {synced_count} articles, {error_count} errors')
            )

    def get_or_create_category(self, name, icon, description, order):
        """Get or create a wiki category."""
        slug = slugify(name)
        category, created = WikiCategory.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'icon': icon,
                'description': description,
                'order': order,
                'is_active': True,
            }
        )

        if created:
            try:
                self.stdout.write(
                    self.style.SUCCESS(f'  Created category: {icon} {name}')
                )
            except UnicodeEncodeError:
                self.stdout.write(
                    self.style.SUCCESS(f'  Created category: {name}')
                )

        return category
