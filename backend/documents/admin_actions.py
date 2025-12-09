"""Django admin actions for bulk upload functionality.

Adds actions to admin interface for:
- Downloading Excel/CSV templates
- Bulk importing data from uploaded files
- Preview mode (dry-run) before committing changes
"""

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from typing import Optional

from .services.bulk_upload_service import BulkUploadService, BulkUploadResult
from .services.template_generator import TemplateGenerator


class BulkUploadAdminMixin:
    """
    Mixin for Django admin classes to add bulk upload functionality.

    Usage:
        @admin.register(HolzartKennzahl)
        class HolzartKennzahlAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
            bulk_upload_model_type = 'holzart'
            bulk_upload_template_required = True
    """

    # Subclass must define these
    bulk_upload_model_type: str = None  # 'holzart', 'oberflaechen', 'komplexitaet', 'material', 'saisonal'
    bulk_upload_template_required: bool = False  # If True, requires template_id in form
    bulk_upload_user_specific: bool = False  # If True, requires user selection

    def get_urls(self):
        """Add custom URLs for bulk upload."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'download-template/',
                self.admin_site.admin_view(self.download_template_view),
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_download_template',
            ),
            path(
                'bulk-upload/',
                self.admin_site.admin_view(self.bulk_upload_view),
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_bulk_upload',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add bulk upload button to changelist."""
        extra_context = extra_context or {}
        extra_context['bulk_upload_url'] = reverse(
            f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_bulk_upload'
        )
        extra_context['download_template_url'] = reverse(
            f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_download_template'
        )
        return super().changelist_view(request, extra_context=extra_context)

    def download_template_view(self, request):
        """Download Excel or CSV template."""
        file_format = request.GET.get('format', 'xlsx')

        generator = TemplateGenerator()

        # Generate appropriate template
        if self.bulk_upload_model_type == 'holzart':
            file_bytes = generator.generate_holzart_template(file_format)
            filename = 'holzarten_template'
        elif self.bulk_upload_model_type == 'oberflaechen':
            file_bytes = generator.generate_oberflaechenbearbeitung_template(file_format)
            filename = 'oberflaechen_template'
        elif self.bulk_upload_model_type == 'komplexitaet':
            file_bytes = generator.generate_komplexitaet_template(file_format)
            filename = 'komplexitaet_template'
        elif self.bulk_upload_model_type == 'material':
            file_bytes = generator.generate_materialliste_template(file_format)
            filename = 'materialliste_template'
        elif self.bulk_upload_model_type == 'saisonal':
            file_bytes = generator.generate_saisonale_marge_template(file_format)
            filename = 'saisonale_marge_template'
        else:
            messages.error(request, 'Unknown model type for template generation')
            return HttpResponseRedirect('..')

        # Prepare response
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_format == 'xlsx' else 'text/csv'
        response = HttpResponse(file_bytes, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}.{file_format}"'

        return response

    def bulk_upload_view(self, request):
        """Handle bulk upload form and processing."""
        from django import forms
        from django.contrib.auth.models import User

        # Define upload form
        class BulkUploadForm(forms.Form):
            file = forms.FileField(
                label='Excel/CSV Datei',
                help_text='Laden Sie eine ausgefüllte Template-Datei hoch (.xlsx oder .csv)'
            )
            dry_run = forms.BooleanField(
                label='Vorschau-Modus (keine Änderungen speichern)',
                required=False,
                initial=True,
                help_text='Aktivieren für Validierung ohne Speichern'
            )
            update_existing = forms.BooleanField(
                label='Bestehende Einträge aktualisieren',
                required=False,
                initial=False,
                help_text='Falls aktiviert, werden vorhandene Einträge überschrieben'
            )

            # Conditional fields
            if self.bulk_upload_template_required:
                from ..betriebskennzahl_models import BetriebskennzahlTemplate
                template = forms.ModelChoiceField(
                    queryset=BetriebskennzahlTemplate.objects.filter(is_active=True),
                    label='Betriebskennzahl Template',
                    required=True,
                    help_text='Wählen Sie das Ziel-Template aus'
                )

            if self.bulk_upload_user_specific:
                user = forms.ModelChoiceField(
                    queryset=User.objects.filter(is_active=True),
                    label='Benutzer/Firma',
                    required=True,
                    help_text='Wählen Sie den Zielbenutzer aus'
                )

        # Process form
        if request.method == 'POST':
            form = BulkUploadForm(request.POST, request.FILES)

            if form.is_valid():
                uploaded_file = request.FILES['file']
                dry_run = form.cleaned_data['dry_run']
                update_existing = form.cleaned_data.get('update_existing', False)

                # Determine file format
                file_format = 'xlsx' if uploaded_file.name.endswith('.xlsx') else 'csv'

                # Read file content
                file_content = uploaded_file.read()

                # Initialize service
                service = BulkUploadService(user=request.user)

                # Process upload based on model type
                result: Optional[BulkUploadResult] = None

                try:
                    if self.bulk_upload_model_type == 'holzart':
                        template_id = form.cleaned_data['template'].id
                        result = service.upload_holzart_kennzahlen(
                            file_content=file_content,
                            template_id=template_id,
                            file_format=file_format,
                            dry_run=dry_run,
                            update_existing=update_existing
                        )

                    elif self.bulk_upload_model_type == 'oberflaechen':
                        template_id = form.cleaned_data['template'].id
                        result = service.upload_oberflaechenbearbeitung_kennzahlen(
                            file_content=file_content,
                            template_id=template_id,
                            file_format=file_format,
                            dry_run=dry_run,
                            update_existing=update_existing
                        )

                    elif self.bulk_upload_model_type == 'komplexitaet':
                        template_id = form.cleaned_data['template'].id
                        result = service.upload_komplexitaet_kennzahlen(
                            file_content=file_content,
                            template_id=template_id,
                            file_format=file_format,
                            dry_run=dry_run,
                            update_existing=update_existing
                        )

                    elif self.bulk_upload_model_type == 'material':
                        user = form.cleaned_data['user']
                        result = service.upload_materialliste(
                            file_content=file_content,
                            user=user,
                            file_format=file_format,
                            dry_run=dry_run,
                            update_existing=update_existing
                        )

                    elif self.bulk_upload_model_type == 'saisonal':
                        user = form.cleaned_data['user']
                        result = service.upload_saisonale_marge(
                            file_content=file_content,
                            user=user,
                            file_format=file_format,
                            dry_run=dry_run
                        )

                    # Display results
                    if result:
                        if result.success and not result.has_errors:
                            mode_text = '(Vorschau)' if dry_run else ''
                            messages.success(
                                request,
                                format_html(
                                    '<strong>✓ Bulk Upload erfolgreich!</strong> {}<br/>'
                                    'Erstellt: {}, Aktualisiert: {}, Übersprungen: {}',
                                    mode_text,
                                    result.created_count,
                                    result.updated_count,
                                    result.skipped_count
                                )
                            )

                            if dry_run:
                                messages.info(
                                    request,
                                    'Vorschau-Modus: Keine Änderungen wurden gespeichert. '
                                    'Deaktivieren Sie "Vorschau-Modus" um die Daten zu speichern.'
                                )
                        else:
                            # Show errors
                            messages.warning(
                                request,
                                format_html(
                                    '<strong>⚠ Bulk Upload mit Fehlern</strong><br/>'
                                    'Erfolgreich: {}, Fehler: {}',
                                    result.total_processed,
                                    len(result.errors)
                                )
                            )

                            # Show first 10 errors
                            for error in result.errors[:10]:
                                messages.error(
                                    request,
                                    f'Zeile {error.row}, Feld "{error.field}": {error.error} (Wert: "{error.value}")'
                                )

                            if len(result.errors) > 10:
                                messages.warning(
                                    request,
                                    f'... und {len(result.errors) - 10} weitere Fehler'
                                )

                        # Redirect on success (non-dry-run)
                        if result.success and not dry_run and not result.has_errors:
                            return HttpResponseRedirect('..')

                except Exception as e:
                    messages.error(request, f'Fehler beim Upload: {str(e)}')

        else:
            form = BulkUploadForm()

        # Render upload form
        context = {
            'form': form,
            'title': f'Bulk Upload: {self.model._meta.verbose_name_plural}',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'site_title': self.admin_site.site_title,
            'site_header': self.admin_site.site_header,
        }

        return render(request, 'admin/bulk_upload_form.html', context)


# =============================================================================
# HELPER FUNCTIONS FOR ADMIN CHANGEFORM
# =============================================================================

def get_bulk_upload_buttons_html(model_name: str, app_label: str = 'documents') -> str:
    """
    Generate HTML for bulk upload buttons to display in admin changelist.

    Usage in admin.py:
        class MyAdmin(admin.ModelAdmin):
            def changelist_view(self, request, extra_context=None):
                extra_context = extra_context or {}
                extra_context['custom_buttons'] = get_bulk_upload_buttons_html('holzartkennzahl')
                return super().changelist_view(request, extra_context)
    """
    download_url = reverse(f'admin:{app_label}_{model_name}_download_template')
    upload_url = reverse(f'admin:{app_label}_{model_name}_bulk_upload')

    return format_html(
        '<div style="margin: 10px 0;">'
        '<a href="{}" class="button" style="margin-right: 10px;">'
        '📥 Template herunterladen (Excel)</a>'
        '<a href="{}?format=csv" class="button" style="margin-right: 10px;">'
        '📥 Template herunterladen (CSV)</a>'
        '<a href="{}" class="button" style="background: #417690; color: white;">'
        '📤 Bulk Upload</a>'
        '</div>',
        download_url,
        download_url,
        upload_url
    )
