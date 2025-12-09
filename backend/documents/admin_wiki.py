"""Django Admin interface for Wiki system."""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.utils.safestring import mark_safe

from .models_wiki import (
    WikiCategory,
    WikiArticle,
    WikiSearchLog,
    WikiFeedback,
)


@admin.register(WikiCategory)
class WikiCategoryAdmin(admin.ModelAdmin):
    """Admin for Wiki Categories."""

    list_display = ('icon_display', 'name', 'article_count_display', 'order', 'status_badge')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'icon', 'description')
        }),
        ('Display', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def icon_display(self, obj):
        """Display icon."""
        return obj.icon
    icon_display.short_description = 'Icon'

    def article_count_display(self, obj):
        """Display article count."""
        count = obj.article_count()
        return f"{count} article{'s' if count != 1 else ''}"
    article_count_display.short_description = 'Articles'

    def status_badge(self, obj):
        """Display active/inactive status."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
                'border-radius: 2px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #95A5A6; color: white; padding: 3px 8px; '
            'border-radius: 2px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'


@admin.register(WikiArticle)
class WikiArticleAdmin(admin.ModelAdmin):
    """Admin for Wiki Articles with sync capabilities."""

    list_display = (
        'status_display',
        'title',
        'category',
        'difficulty_badge',
        'view_count_display',
        'helpfulness_display',
        'updated_at_display'
    )
    list_filter = ('is_published', 'is_featured', 'difficulty', 'category', 'updated_at')
    search_fields = ('title', 'summary', 'content', 'keywords')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('related_articles',)
    date_hierarchy = 'updated_at'

    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'category', 'difficulty')
        }),
        ('Content', {
            'fields': ('summary', 'content'),
            'description': 'Content supports Markdown formatting'
        }),
        ('Metadata', {
            'fields': ('estimated_time', 'keywords', 'related_articles')
        }),
        ('Publishing', {
            'fields': ('is_published', 'is_featured', 'published_at')
        }),
        ('Source Sync', {
            'fields': ('source_file', 'last_synced_at'),
            'classes': ('collapse',),
            'description': 'Auto-sync from markdown files'
        }),
        ('Analytics', {
            'fields': ('view_count', 'helpful_count', 'not_helpful_count'),
            'classes': ('collapse',)
        }),
        ('Authorship', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = (
        'content_html',
        'view_count',
        'helpful_count',
        'not_helpful_count',
        'created_at',
        'updated_at',
        'published_at',
        'last_synced_at'
    )

    actions = ['publish_articles', 'unpublish_articles', 'feature_articles', 'sync_from_source']

    def get_urls(self):
        """Add custom URLs."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'wiki-home/',
                self.admin_site.admin_view(self.wiki_home_view),
                name='documents_wiki_home',
            ),
            path(
                '<int:article_id>/preview/',
                self.admin_site.admin_view(self.preview_article_view),
                name='documents_wikiarticle_preview',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add wiki home button to changelist."""
        extra_context = extra_context or {}
        extra_context['wiki_home_url'] = reverse('admin:documents_wiki_home')
        return super().changelist_view(request, extra_context=extra_context)

    def wiki_home_view(self, request):
        """Wiki home page showing all categories and featured articles."""
        categories = WikiCategory.objects.filter(is_active=True).prefetch_related('articles')
        featured = WikiArticle.objects.filter(is_published=True, is_featured=True)[:5]
        popular = WikiArticle.objects.filter(is_published=True).order_by('-view_count')[:5]
        recent = WikiArticle.objects.filter(is_published=True).order_by('-updated_at')[:5]

        # Search
        query = request.GET.get('q', '')
        search_results = []
        if query:
            search_results = WikiArticle.objects.filter(
                Q(title__icontains=query) |
                Q(summary__icontains=query) |
                Q(content__icontains=query) |
                Q(keywords__icontains=query),
                is_published=True
            )

            # Log search
            WikiSearchLog.objects.create(
                query=query,
                results_count=search_results.count(),
                user=request.user if request.user.is_authenticated else None
            )

        context = {
            'title': 'How-To Wiki',
            'categories': categories,
            'featured': featured,
            'popular': popular,
            'recent': recent,
            'query': query,
            'search_results': search_results,
            'opts': self.model._meta,
            'has_view_permission': True,
            'site_title': self.admin_site.site_title,
            'site_header': self.admin_site.site_header,
        }

        return render(request, 'admin/wiki_home.html', context)

    def preview_article_view(self, request, article_id):
        """Preview article."""
        article = WikiArticle.objects.get(pk=article_id)
        article.increment_view()

        context = {
            'title': article.title,
            'article': article,
            'opts': self.model._meta,
            'has_view_permission': True,
            'site_title': self.admin_site.site_title,
            'site_header': self.admin_site.site_header,
        }

        return render(request, 'admin/wiki_article.html', context)

    # List display methods

    def status_display(self, obj):
        """Display publication status with icons."""
        published = "✓" if obj.is_published else "✗"
        featured = "⭐" if obj.is_featured else ""
        return f"{published} {featured}"
    status_display.short_description = 'Status'

    def difficulty_badge(self, obj):
        """Display difficulty as badge."""
        colors = {
            'beginner': '#27AE60',
            'intermediate': '#F39C12',
            'advanced': '#E74C3C',
        }
        color = colors.get(obj.difficulty, '#95A5A6')
        display = obj.get_difficulty_display().split(' - ')[0]  # Just the emoji + level
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            display
        )
    difficulty_badge.short_description = 'Difficulty'

    def view_count_display(self, obj):
        """Display view count."""
        return f"👁 {obj.view_count}"
    view_count_display.short_description = 'Views'

    def helpfulness_display(self, obj):
        """Display helpfulness score."""
        score = obj.helpfulness_score
        if score is None:
            return "—"

        if score >= 80:
            color = '#27AE60'
            icon = '👍'
        elif score >= 50:
            color = '#F39C12'
            icon = '👌'
        else:
            color = '#E74C3C'
            icon = '👎'

        return format_html(
            '<span style="color: {};">{} {:.0f}%</span>',
            color,
            icon,
            score
        )
    helpfulness_display.short_description = 'Helpful'

    def updated_at_display(self, obj):
        """Display last update time."""
        return obj.updated_at.strftime('%d.%m.%Y')
    updated_at_display.short_description = 'Updated'

    # Actions

    def publish_articles(self, request, queryset):
        """Publish selected articles."""
        count = queryset.update(is_published=True)
        messages.success(request, f'{count} article(s) published.')
    publish_articles.short_description = 'Publish selected articles'

    def unpublish_articles(self, request, queryset):
        """Unpublish selected articles."""
        count = queryset.update(is_published=False)
        messages.success(request, f'{count} article(s) unpublished.')
    unpublish_articles.short_description = 'Unpublish selected articles'

    def feature_articles(self, request, queryset):
        """Feature selected articles."""
        count = queryset.update(is_featured=True)
        messages.success(request, f'{count} article(s) featured.')
    feature_articles.short_description = 'Feature selected articles'

    def sync_from_source(self, request, queryset):
        """Sync selected articles from source files."""
        from .management.commands.sync_wiki import sync_article
        synced = 0
        errors = []

        for article in queryset:
            try:
                if article.source_file:
                    sync_article(article)
                    synced += 1
            except Exception as e:
                errors.append(f"{article.title}: {str(e)}")

        if synced:
            messages.success(request, f'{synced} article(s) synced from source.')
        if errors:
            messages.error(request, f'Errors: {", ".join(errors)}')
    sync_from_source.short_description = 'Sync from source files'

    # Save methods

    def save_model(self, request, obj, form, change):
        """Set authorship on save."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WikiSearchLog)
class WikiSearchLogAdmin(admin.ModelAdmin):
    """Admin for search analytics."""

    list_display = ('query', 'results_count_display', 'user', 'searched_at_display')
    list_filter = ('searched_at', 'results_count')
    search_fields = ('query',)
    date_hierarchy = 'searched_at'
    readonly_fields = ('query', 'results_count', 'user', 'searched_at')

    def has_add_permission(self, request):
        """Prevent manual creation."""
        return False

    def results_count_display(self, obj):
        """Display result count with icon."""
        if obj.results_count == 0:
            return format_html('<span style="color: #E74C3C;">❌ 0 results</span>')
        elif obj.results_count < 3:
            return format_html('<span style="color: #F39C12;">⚠️ {} results</span>', obj.results_count)
        else:
            return format_html('<span style="color: #27AE60;">✓ {} results</span>', obj.results_count)
    results_count_display.short_description = 'Results'

    def searched_at_display(self, obj):
        """Display search time."""
        return obj.searched_at.strftime('%d.%m.%Y %H:%M')
    searched_at_display.short_description = 'When'


@admin.register(WikiFeedback)
class WikiFeedbackAdmin(admin.ModelAdmin):
    """Admin for user feedback."""

    list_display = ('article', 'feedback_badge', 'user', 'comment_preview', 'created_at_display')
    list_filter = ('is_helpful', 'created_at', 'article__category')
    search_fields = ('comment', 'article__title')
    date_hierarchy = 'created_at'
    readonly_fields = ('article', 'is_helpful', 'user', 'created_at')

    def has_add_permission(self, request):
        """Prevent manual creation."""
        return False

    def feedback_badge(self, obj):
        """Display helpful/not helpful badge."""
        if obj.is_helpful:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
                'border-radius: 2px;">👍 Helpful</span>'
            )
        return format_html(
            '<span style="background-color: #E74C3C; color: white; padding: 3px 8px; '
            'border-radius: 2px;">👎 Not Helpful</span>'
        )
    feedback_badge.short_description = 'Feedback'

    def comment_preview(self, obj):
        """Display comment preview."""
        if not obj.comment:
            return "—"
        preview = obj.comment[:50]
        if len(obj.comment) > 50:
            preview += "..."
        return preview
    comment_preview.short_description = 'Comment'

    def created_at_display(self, obj):
        """Display feedback time."""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_display.short_description = 'When'
