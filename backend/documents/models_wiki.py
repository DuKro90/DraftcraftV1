"""Wiki system for Django Admin - How-to guides and documentation.

Provides in-admin documentation with:
- Searchable guides
- Category organization
- Version tracking
- Automatic updates from markdown files
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator
import markdown


class WikiCategory(models.Model):
    """Categories for organizing wiki articles."""

    CATEGORY_ICONS = [
        ('📚', 'Books - General Documentation'),
        ('🚀', 'Rocket - Getting Started'),
        ('📤', 'Upload - Data Import/Export'),
        ('⚙️', 'Settings - Configuration'),
        ('🧪', 'Test Tube - Testing'),
        ('🐛', 'Bug - Troubleshooting'),
        ('💡', 'Lightbulb - Tips & Tricks'),
        ('🔧', 'Wrench - Advanced Features'),
        ('📊', 'Chart - Reports & Analytics'),
        ('🔐', 'Lock - Security & Permissions'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Category name (e.g., "Getting Started", "Data Import")'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text='URL-friendly version (auto-generated from name)'
    )
    icon = models.CharField(
        max_length=10,
        choices=CATEGORY_ICONS,
        default='📚',
        help_text='Icon to display in admin'
    )
    description = models.TextField(
        blank=True,
        help_text='Brief description of this category'
    )
    order = models.IntegerField(
        default=0,
        help_text='Display order (lower numbers appear first)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Hide category if inactive'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Wiki Category'
        verbose_name_plural = 'Wiki Categories'

    def __str__(self):
        return f"{self.icon} {self.name}"

    def article_count(self):
        """Count of active articles in this category."""
        return self.articles.filter(is_published=True).count()


class WikiArticle(models.Model):
    """Individual wiki articles/guides."""

    DIFFICULTY_CHOICES = [
        ('beginner', '🟢 Beginner - Easy to follow'),
        ('intermediate', '🟡 Intermediate - Some experience needed'),
        ('advanced', '🔴 Advanced - Expert level'),
    ]

    # Basic info
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)],
        help_text='Article title (clear and descriptive)'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text='URL-friendly version'
    )
    category = models.ForeignKey(
        WikiCategory,
        on_delete=models.PROTECT,
        related_name='articles',
        help_text='Category for organization'
    )

    # Content
    summary = models.TextField(
        max_length=500,
        help_text='Short summary (appears in article list)'
    )
    content = models.TextField(
        help_text='Full article content (Markdown supported)'
    )
    content_html = models.TextField(
        blank=True,
        editable=False,
        help_text='Auto-generated HTML from Markdown'
    )

    # Metadata
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner',
        help_text='Difficulty level'
    )
    estimated_time = models.CharField(
        max_length=50,
        blank=True,
        help_text='Estimated reading time (e.g., "5 minutes", "10-15 minutes")'
    )
    keywords = models.CharField(
        max_length=200,
        blank=True,
        help_text='Comma-separated keywords for search (e.g., "upload, excel, import")'
    )

    # Related content
    related_articles = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        help_text='Related articles to show at the end'
    )

    # Source tracking (for auto-sync)
    source_file = models.CharField(
        max_length=500,
        blank=True,
        help_text='Original markdown file path (for auto-sync)'
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time synced from source file'
    )

    # Publishing
    is_published = models.BooleanField(
        default=True,
        help_text='Show article to users'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text='Show in featured section on wiki home'
    )

    # Analytics
    view_count = models.IntegerField(
        default=0,
        editable=False,
        help_text='Number of times viewed'
    )
    helpful_count = models.IntegerField(
        default=0,
        editable=False,
        help_text='Number of "helpful" votes'
    )
    not_helpful_count = models.IntegerField(
        default=0,
        editable=False,
        help_text='Number of "not helpful" votes'
    )

    # Authorship
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='wiki_articles_created',
        help_text='Article author'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='wiki_articles_updated',
        help_text='Last person to update'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When article was first published'
    )

    class Meta:
        ordering = ['-is_featured', '-updated_at']
        verbose_name = 'Wiki Article'
        verbose_name_plural = 'Wiki Articles'
        indexes = [
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['slug']),
            models.Index(fields=['-view_count']),
        ]

    def __str__(self):
        status = "✓" if self.is_published else "✗"
        featured = "⭐" if self.is_featured else ""
        return f"{status} {featured} {self.title}"

    def save(self, *args, **kwargs):
        """Auto-generate HTML from Markdown on save."""
        if self.content:
            # Convert Markdown to HTML
            self.content_html = markdown.markdown(
                self.content,
                extensions=[
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.tables',
                    'markdown.extensions.toc',
                    'markdown.extensions.codehilite',
                ]
            )

        # Set published_at on first publish
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def increment_view(self):
        """Increment view counter (use F() to avoid race conditions)."""
        from django.db.models import F
        WikiArticle.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)

    def mark_helpful(self):
        """User marked article as helpful."""
        from django.db.models import F
        WikiArticle.objects.filter(pk=self.pk).update(helpful_count=F('helpful_count') + 1)

    def mark_not_helpful(self):
        """User marked article as not helpful."""
        from django.db.models import F
        WikiArticle.objects.filter(pk=self.pk).update(not_helpful_count=F('not_helpful_count') + 1)

    @property
    def helpfulness_score(self):
        """Calculate helpfulness percentage."""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return None
        return (self.helpful_count / total) * 100

    @property
    def reading_time_minutes(self):
        """Estimate reading time (200 words per minute)."""
        if not self.content:
            return 0
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))


class WikiSearchLog(models.Model):
    """Log searches to improve content and SEO."""

    query = models.CharField(
        max_length=200,
        help_text='Search query'
    )
    results_count = models.IntegerField(
        default=0,
        help_text='Number of results found'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who searched (if logged in)'
    )
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-searched_at']
        verbose_name = 'Wiki Search Log'
        verbose_name_plural = 'Wiki Search Logs'
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['-searched_at']),
        ]

    def __str__(self):
        return f'"{self.query}" ({self.results_count} results)'


class WikiFeedback(models.Model):
    """User feedback on articles."""

    article = models.ForeignKey(
        WikiArticle,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    is_helpful = models.BooleanField(
        help_text='Was this article helpful?'
    )
    comment = models.TextField(
        blank=True,
        help_text='Optional feedback comment'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wiki Feedback'
        verbose_name_plural = 'Wiki Feedback'

    def __str__(self):
        status = "👍 Helpful" if self.is_helpful else "👎 Not Helpful"
        return f"{status} - {self.article.title}"
