# Multi-Language Implementation Guide (DE/EN)

**Status:** Framework configured, Translation files need to be generated
**Date:** December 03, 2025

---

## ✅ Was bereits implementiert ist:

### 1. Django i18n Framework
- ✅ `LocaleMiddleware` aktiviert in `config/settings/base.py`
- ✅ Sprachen konfiguriert: Deutsch (de) & English (en)
- ✅ Locale paths definiert: `backend/locale/`
- ✅ Template context processor aktiviert
- ✅ Language switcher template erstellt

### 2. Konfiguration in settings.py
```python
LANGUAGE_CODE = 'de'  # Default
LANGUAGES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
]
LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]
```

---

## 🚀 Nächste Schritte (Anleitung):

### Schritt 1: Locale-Verzeichnis erstellen
```bash
cd C:\Codes\DraftcraftV1\backend
mkdir locale
```

### Schritt 2: URLs für Language Switching hinzufügen

Füge zu `config/urls.py` hinzu:
```python
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

urlpatterns = [
    path('i18n/setlang/', set_language, name='set_language'),
    # ... existing patterns
]
```

### Schritt 3: Strings markieren für Übersetzung

**In Python Code:**
```python
from django.utils.translation import gettext_lazy as _

# Model verbose names
class WikiArticle(models.Model):
    class Meta:
        verbose_name = _("Wiki Article")
        verbose_name_plural = _("Wiki Articles")

# Help text
title = models.CharField(
    max_length=200,
    help_text=_("Article title (clear and descriptive)")
)
```

**In Templates:**
```django
{% load i18n %}

<h1>{% trans "How-To Wiki" %}</h1>
<p>{% trans "Comprehensive guides and documentation" %}</p>

{% comment %}Oder mit Variablen{% endcomment %}
{% blocktrans count counter=articles.count %}
There is {{ counter }} article.
{% plural %}
There are {{ counter }} articles.
{% endblocktrans %}
```

### Schritt 4: Translation Files generieren
```bash
cd C:\Codes\DraftcraftV1\backend

# Für jede App
python manage.py makemessages -l de
python manage.py makemessages -l en

# Oder alle auf einmal
python manage.py makemessages -l de -l en --ignore=venv
```

Dies erstellt:
```
backend/
├── locale/
│   ├── de/
│   │   └── LC_MESSAGES/
│   │       ├── django.po  # Deutsche Übersetzungen
│   │       └── django.mo  # Kompiliert
│   └── en/
│       └── LC_MESSAGES/
│           ├── django.po  # Englische Übersetzungen
│           └── django.mo  # Kompiliert
```

### Schritt 5: Übersetzungen eintragen

Öffne `locale/de/LC_MESSAGES/django.po` und übersetze:
```po
#: models.py:123
msgid "Wiki Article"
msgstr "Wiki-Artikel"

#: models.py:125
msgid "Article title (clear and descriptive)"
msgstr "Artikel-Titel (klar und beschreibend)"
```

Öffne `locale/en/LC_MESSAGES/django.po`:
```po
#: models.py:123
msgid "Wiki Article"
msgstr "Wiki Article"  # Englisch (meist gleich wie msgid)

#: models.py:125
msgid "Article title (clear and descriptive)"
msgstr "Article title (clear and descriptive)"
```

### Schritt 6: Translations kompilieren
```bash
python manage.py compilemessages
```

### Schritt 7: Language Switcher in Admin Base Template einfügen

Erstelle/Bearbeite `backend/documents/templates/admin/base_site.html`:
```django
{% extends "admin/base.html" %}
{% load i18n %}

{% block title %}{% trans "DraftCraft Admin" %}{% endblock %}

{% block branding %}
<h1 id="site-name">
    <a href="{% url 'admin:index' %}">
        {% trans "DraftCraft Administration" %}
    </a>
</h1>
{% endblock %}

{% block userlinks %}
{% include "admin/language_switcher.html" %}
{{ block.super }}
{% endblock %}
```

---

## 📝 Wichtige Strings zum Übersetzen:

### Wiki System
```python
# models_wiki.py
_("Wiki Category")
_("Wiki Categories")
_("Wiki Article")
_("Wiki Articles")
_("Search Log")
_("Feedback")

# Kategorien
_("Getting Started")
_("Data Import & Export")
_("Configuration")
_("Troubleshooting")
_("Advanced Features")

# Schwierigkeitsgrade
_("Beginner - Easy to follow")
_("Intermediate - Some experience needed")
_("Advanced - Expert level")
```

### Bulk Upload
```python
_("Template herunterladen")  # Download template
_("Bulk Upload")
_("Excel/CSV Datei")
_("Vorschau-Modus")  # Preview mode
_("Bestehende Einträge aktualisieren")  # Update existing
```

### Admin Interface
```python
_("Status")
_("Active")
_("Inactive")
_("Created")
_("Updated")
_("Published")
_("Unpublished")
_("Helpful")
_("Not Helpful")
```

---

## 🎨 Beispiel: Vollständig übersetztes Model

**Vorher:**
```python
class WikiArticle(models.Model):
    title = models.CharField(max_length=200, help_text='Article title')

    class Meta:
        verbose_name = 'Wiki Article'
```

**Nachher:**
```python
from django.utils.translation import gettext_lazy as _

class WikiArticle(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
        help_text=_('Article title (clear and descriptive)')
    )

    class Meta:
        verbose_name = _('Wiki Article')
        verbose_name_plural = _('Wiki Articles')
```

---

## 🔄 Workflow für neue Features:

1. **Code schreiben** mit `_()`-Markierungen
2. **Messages generieren:** `python manage.py makemessages -l de -l en`
3. **Übersetzen:** `.po` Dateien bearbeiten
4. **Kompilieren:** `python manage.py compilemessages`
5. **Testen:** Server neu starten, Sprache wechseln

---

## 🧪 Testing:

```bash
# Server starten
python manage.py runserver

# Im Admin einloggen
http://localhost:8000/admin/

# Sprache wechseln mit Dropdown (oben rechts)
# Oder URL Parameter:
http://localhost:8000/admin/?language=de
http://localhost:8000/admin/?language=en
```

---

## 💡 Best Practices:

### 1. Immer `gettext_lazy` verwenden
```python
from django.utils.translation import gettext_lazy as _

# ✅ Gut (lazy evaluation)
verbose_name = _("Title")

# ❌ Schlecht (wird sofort evaluiert)
from django.utils.translation import gettext
verbose_name = gettext("Title")
```

### 2. Kontext-spezifische Übersetzungen
```python
from django.utils.translation import pgettext_lazy

# Unterschiedliche Übersetzungen für gleiches Wort
status = pgettext_lazy("document status", "Draft")
status = pgettext_lazy("payment status", "Draft")
```

### 3. Pluralisierung
```django
{% blocktrans count counter=items.count %}
There is {{ counter }} item.
{% plural %}
There are {{ counter }} items.
{% endblocktrans %}
```

### 4. Variablen in Strings
```python
from django.utils.translation import gettext as _

message = _("Welcome, %(username)s!") % {'username': user.username}

# Oder in Templates:
{% blocktrans with username=user.username %}
Welcome, {{ username }}!
{% endblocktrans %}
```

---

## 📊 Umfang der Übersetzungsarbeit:

### Bereits i18n-ready (müssen nur übersetzt werden):
- Django Admin Interface (automatisch)
- Django Auth System (automatisch)
- DRF Messages (automatisch via rest_framework.locale)

### Muss manuell übersetzt werden:
- **documents/models.py** (~50 Strings)
- **documents/models_wiki.py** (~40 Strings)
- **documents/admin.py** (~30 Strings)
- **documents/admin_wiki.py** (~25 Strings)
- **documents/forms.py** (~100 Strings - Tooltips!)
- **extraction/models.py** (~30 Strings)
- **Wiki Templates** (~50 Strings)
- **Bulk Upload Templates** (~30 Strings)

**Gesamt:** ~355 Strings zu übersetzen

**Geschätzte Zeit:** 3-4 Stunden für komplette Übersetzung

---

## 🛠️ Tools für schnellere Übersetzung:

### 1. Poedit (Empfohlen)
```
Download: https://poedit.net/
- GUI für .po Dateien
- Auto-Translation vorschläge
- Syntax checking
```

### 2. Django Rosetta (Web-basiert)
```bash
pip install django-rosetta

# In INSTALLED_APPS:
'rosetta',

# In urls.py:
path('rosetta/', include('rosetta.urls')),

# Dann: http://localhost:8000/rosetta/
```

### 3. Google Translate API (Automatisch)
```python
# Für initiale Übersetzungen, danach manuell prüfen
from googletrans import Translator

translator = Translator()
result = translator.translate('Hello', dest='de')
print(result.text)  # 'Hallo'
```

---

## 🎯 Quick Start (Minimal Implementation):

### Nur die wichtigsten 20 Strings übersetzen:

1. **Admin Navigation:**
   - "Documents", "Wiki Articles", "Bulk Upload"

2. **Wiki Homepage:**
   - "How-To Wiki", "Search", "Featured", "Popular", "Categories"

3. **Common Actions:**
   - "Save", "Delete", "Cancel", "Edit", "View", "Add"

4. **Status:**
   - "Active", "Inactive", "Published", "Draft"

### Minimal .po Datei (de):
```po
msgid "How-To Wiki"
msgstr "Anleitungs-Wiki"

msgid "Search"
msgstr "Suchen"

msgid "Featured"
msgstr "Empfohlen"

msgid "Save"
msgstr "Speichern"

msgid "Active"
msgstr "Aktiv"
```

---

## 📋 Checkliste:

- [x] Django i18n konfiguriert
- [x] Middleware aktiviert
- [x] Language switcher template erstellt
- [ ] URLs für language switching hinzugefügt
- [ ] Strings in Code mit `_()` markiert
- [ ] Translation files generiert
- [ ] Deutsche Übersetzungen eingetragen
- [ ] Englische Übersetzungen eingetragen
- [ ] Messages kompiliert
- [ ] Language switcher in Admin eingebunden
- [ ] Testing durchgeführt

---

## 🔗 Nützliche Links:

- [Django i18n Documentation](https://docs.djangoproject.com/en/5.0/topics/i18n/)
- [Translation Tutorial](https://docs.djangoproject.com/en/5.0/topics/i18n/translation/)
- [Poedit Download](https://poedit.net/)
- [Django Rosetta](https://github.com/mbi/django-rosetta)

---

**Status:** Framework configured ✅
**Next:** Run `makemessages` and start translating!

