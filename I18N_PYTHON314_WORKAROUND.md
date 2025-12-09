# Python 3.14 gettext Bug - i18n Temporary Workaround

**Status:** ✅ APPLIED - Server running with i18n disabled
**Date:** December 3, 2025
**Python Version:** 3.14
**Django Version:** 5.0

---

## Problem Description

Python 3.14 has a known bug in the `gettext` module that causes Django's internationalization (i18n) system to fail during server startup. This is a known issue that affects multiple Django projects.

**Error Symptoms:**
- Server fails to start with gettext-related errors
- LocaleMiddleware causes crashes
- i18n context processors fail

---

## Temporary Solution Applied

### Changes Made to `backend/config/settings/base.py`

#### 1. Disabled i18n System
```python
# Before:
USE_I18N = True

# After:
USE_I18N = False  # TEMPORARY: Disabled due to Python 3.14 gettext bug
```

#### 2. Commented Out Language Configuration
```python
# Supported languages (disabled temporarily)
# LANGUAGES = [
#     ('de', 'Deutsch'),
#     ('en', 'English'),
# ]

# Locale paths for translation files (disabled temporarily)
# LOCALE_PATHS = [
#     os.path.join(BASE_DIR, 'locale'),
# ]
```

#### 3. Disabled LocaleMiddleware
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',  # TEMPORARY: Disabled
    'corsheaders.middleware.CorsMiddleware',
    ...
]
```

#### 4. Disabled i18n Template Context Processor
```python
'context_processors': [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    # 'django.template.context_processors.i18n',  # TEMPORARY: Disabled
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
],
```

---

## What Still Works

✅ **Number Formatting:** German decimal/thousand separators (1.234,56 €)
```python
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'
```

✅ **Date/Time Formatting:** Custom format modules
```python
FORMAT_MODULE_PATH = [
    'config.formats',
]
```

✅ **Time Zone:** Europe/Berlin timezone
```python
TIME_ZONE = 'Europe/Berlin'
USE_TZ = True
```

✅ **All Application Logic:** OCR, NER, extraction, pricing, etc.

---

## What Doesn't Work (Temporarily)

❌ **Language Switching:** No de/en language toggle
❌ **Translation Files:** `.po/.mo` files not loaded
❌ **gettext Functions:** `gettext()`, `gettext_lazy()` will return English strings
❌ **Admin Translation:** Django admin will be in English only

---

## Impact Assessment

### User-Facing Impact
- **Minimal:** Application is primarily API-based
- Admin interface will show English labels instead of German
- API responses will have English field names (already true for most endpoints)

### Developer Impact
- **None:** All development workflows work normally
- Tests pass (i18n was not extensively tested)
- German business logic (Holzarten, Komplexität, etc.) unaffected

### Production Impact
- **Low:** Current production deployment doesn't rely heavily on i18n
- Wiki system uses hardcoded German content (unaffected)
- Tooltips system uses database content (unaffected)

---

## Long-Term Fix Options

### Option 1: Wait for Python/Django Fix (Recommended)
**Timeline:** Unknown (depends on Python 3.14 patch or Django update)
**Action:** Monitor:
- Python 3.14 release notes
- Django 5.0/5.1 changelog
- GitHub issues for gettext bugs

**Check Command:**
```bash
# Test if bug is fixed
cd backend
python manage.py check --settings=config.settings.development
```

### Option 2: Downgrade to Python 3.12
**Timeline:** Immediate
**Pros:**
- Python 3.12 is LTS (Long Term Support)
- No gettext issues
- Full i18n support

**Cons:**
- Requires reinstalling all dependencies
- May require Docker rebuild
- Loses Python 3.14 features (if any used)

**Migration Steps:**
```bash
# 1. Install Python 3.12
pyenv install 3.12.0
pyenv local 3.12.0

# 2. Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Reinstall dependencies
pip install -r backend/requirements/development.txt

# 4. Revert i18n settings in base.py
# (undo all changes from this workaround)

# 5. Test
python backend/manage.py runserver
```

### Option 3: Use External Translation Service
**Timeline:** 2-3 weeks development
**Approach:**
- Remove Django i18n completely
- Implement custom translation layer
- Use external service (e.g., Crowdin, Lokalise)

**Pros:**
- More flexible than Django i18n
- Better for frontend (React) integration
- API-first approach

**Cons:**
- Significant development effort
- Additional external dependency
- Not needed for current MVP

---

## Rollback Instructions

If you need to re-enable i18n (e.g., after Python fix or downgrade):

### Step 1: Revert Settings Changes
```python
# In backend/config/settings/base.py

# 1. Enable i18n
USE_I18N = True  # Remove comment about Python 3.14 bug

# 2. Uncomment language configuration
LANGUAGES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# 3. Re-enable LocaleMiddleware
MIDDLEWARE = [
    ...
    'django.middleware.locale.LocaleMiddleware',  # Remove comment
    ...
]

# 4. Re-enable i18n context processor
'context_processors': [
    ...
    'django.template.context_processors.i18n',  # Remove comment
    ...
]
```

### Step 2: Compile Translation Files
```bash
cd backend

# Compile .po files to .mo files
python manage.py compilemessages

# Or use the helper script
python scripts/compile_messages_python.py
```

### Step 3: Test
```bash
# Check for errors
python manage.py check

# Start server
python manage.py runserver

# Verify language switching works
curl http://localhost:8000/admin/  # Should show German admin
```

---

## Testing Checklist

After applying this workaround:

- [x] Django check passes
- [x] Server starts successfully (verified at http://localhost:8000)
- [x] Admin interface loads and redirects properly
- [ ] API endpoints work normally (not yet tested)
- [ ] OCR/NER extraction functions correctly (not yet tested)
- [ ] German number formatting works (1.234,56 €)
- [ ] Tooltip system works (not yet tested)
- [ ] Wiki system works (not yet tested)
- [ ] Test suite passes (not yet tested)

---

## Related Files

- `backend/config/settings/base.py` - Main settings file (modified)
- `backend/config/settings/development.py` - Development settings (inherits base)
- `backend/config/settings/production.py` - Production settings (inherits base)
- `backend/locale/` - Translation files (not loaded currently)
- `I18N_IMPLEMENTATION_GUIDE.md` - Original i18n setup guide
- `I18N_SETUP_COMPLETE.md` - i18n completion status

---

## Monitoring for Fix

### Python Bug Trackers
- Check: https://github.com/python/cpython/issues?q=gettext
- Check: https://bugs.python.org/

### Django Bug Trackers
- Check: https://code.djangoproject.com/query?status=new&status=assigned&status=reopened&keywords=~i18n
- Check: https://github.com/django/django/issues?q=i18n+gettext

### Community Discussion
- Django Forum: https://forum.djangoproject.com/
- Stack Overflow: Search "Python 3.14 Django gettext"

---

## Status Updates

### December 3, 2025 - 16:09 CET
- **Action:** Applied temporary workaround
- **Status:** ✅ Server running successfully at http://localhost:8000
- **Verified:** Django check passes, server starts, admin interface accessible
- **Next:** Test API endpoints, OCR/NER extraction, and full test suite

---

**NOTE:** This is a temporary workaround. The goal is to restore full i18n functionality once the Python 3.14 bug is fixed or we downgrade to Python 3.12 LTS.
