# Generated manually for Supabase RLS security compliance
# This migration only runs on Supabase (production), not on test databases
from django.db import migrations
from django.conf import settings


def enable_rls_if_supabase(apps, schema_editor):
    """
    Enable RLS only if running on Supabase (production database).
    Skip for test databases or local development to avoid test failures.
    """
    # Check if we're running on Supabase
    db_name = schema_editor.connection.settings_dict.get('NAME', '')

    # Skip RLS for test databases (they start with 'test_')
    if db_name.startswith('test_'):
        print("⏭️  Skipping RLS migration for test database")
        return

    # Skip if not using Supabase host
    db_host = schema_editor.connection.settings_dict.get('HOST', '')
    if 'supabase.co' not in db_host:
        print(f"⏭️  Skipping RLS migration for local development (host: {db_host})")
        return

    print("✅ Applying RLS security for Supabase production database")

    # Enable RLS and create policies
    schema_editor.execute("""
        -- Enable Row Level Security on Django core tables
        ALTER TABLE IF EXISTS django_migrations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS django_content_type ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS django_admin_log ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS django_session ENABLE ROW LEVEL SECURITY;

        -- Enable RLS on Django auth tables
        ALTER TABLE IF EXISTS auth_permission ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_group ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_group_permissions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_user ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_user_groups ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_user_user_permissions ENABLE ROW LEVEL SECURITY;

        -- Enable RLS on documents app tables
        ALTER TABLE IF EXISTS documents_document ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_auditlog ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_extractionresult ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_adminactionaudit ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_batch ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_batchdocument ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_betriebskennzahltemplate ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_extractionfailurepattern ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_holzartkennzahl ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_individuellebetriebskennzahl ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_komplexitaetkennzahl ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_materiallisteposition ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_oberflächenbearbeitungkennzahl ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_patternreviewsession ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_patternfixproposal ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_saisonalemarge ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_calculationexplanation ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_calculationfactor ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_userprojectbenchmark ENABLE ROW LEVEL SECURITY;

        -- Enable RLS on extraction app tables
        ALTER TABLE IF EXISTS extraction_extractionconfig ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS extraction_materialextraction ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS extraction_extractedentity ENABLE ROW LEVEL SECURITY;

        -- Enable RLS on proposals app tables
        ALTER TABLE IF EXISTS proposals_proposal ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS proposals_proposaltemplate ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS proposals_proposalline ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS proposals_proposalcalculationlog ENABLE ROW LEVEL SECURITY;

        -- Create RLS policies for service role (Django backend access)
        -- Drop existing policies if they exist (for idempotency)
        DO $$
        BEGIN
            -- Django core tables
            DROP POLICY IF EXISTS "Service role full access" ON django_migrations;
            DROP POLICY IF EXISTS "Service role full access" ON django_content_type;
            DROP POLICY IF EXISTS "Service role full access" ON django_admin_log;
            DROP POLICY IF EXISTS "Service role full access" ON django_session;

            -- Auth tables
            DROP POLICY IF EXISTS "Service role full access" ON auth_permission;
            DROP POLICY IF EXISTS "Service role full access" ON auth_group;
            DROP POLICY IF EXISTS "Service role full access" ON auth_group_permissions;
            DROP POLICY IF EXISTS "Service role full access" ON auth_user;
            DROP POLICY IF EXISTS "Service role full access" ON auth_user_groups;
            DROP POLICY IF EXISTS "Service role full access" ON auth_user_user_permissions;

            -- Documents tables
            DROP POLICY IF EXISTS "Service role full access" ON documents_document;
            DROP POLICY IF EXISTS "Service role full access" ON documents_auditlog;
            DROP POLICY IF EXISTS "Service role full access" ON documents_extractionresult;
            DROP POLICY IF EXISTS "Service role full access" ON documents_adminactionaudit;
            DROP POLICY IF EXISTS "Service role full access" ON documents_batch;
            DROP POLICY IF EXISTS "Service role full access" ON documents_batchdocument;
            DROP POLICY IF EXISTS "Service role full access" ON documents_betriebskennzahltemplate;
            DROP POLICY IF EXISTS "Service role full access" ON documents_extractionfailurepattern;
            DROP POLICY IF EXISTS "Service role full access" ON documents_holzartkennzahl;
            DROP POLICY IF EXISTS "Service role full access" ON documents_individuellebetriebskennzahl;
            DROP POLICY IF EXISTS "Service role full access" ON documents_komplexitaetkennzahl;
            DROP POLICY IF EXISTS "Service role full access" ON documents_materiallisteposition;
            DROP POLICY IF EXISTS "Service role full access" ON documents_oberflächenbearbeitungkennzahl;
            DROP POLICY IF EXISTS "Service role full access" ON documents_patternreviewsession;
            DROP POLICY IF EXISTS "Service role full access" ON documents_patternfixproposal;
            DROP POLICY IF EXISTS "Service role full access" ON documents_saisonalemarge;
            DROP POLICY IF EXISTS "Service role full access" ON documents_calculationexplanation;
            DROP POLICY IF EXISTS "Service role full access" ON documents_calculationfactor;
            DROP POLICY IF EXISTS "Service role full access" ON documents_userprojectbenchmark;

            -- Extraction tables
            DROP POLICY IF EXISTS "Service role full access" ON extraction_extractionconfig;
            DROP POLICY IF EXISTS "Service role full access" ON extraction_materialextraction;
            DROP POLICY IF EXISTS "Service role full access" ON extraction_extractedentity;

            -- Proposals tables
            DROP POLICY IF EXISTS "Service role full access" ON proposals_proposal;
            DROP POLICY IF EXISTS "Service role full access" ON proposals_proposaltemplate;
            DROP POLICY IF EXISTS "Service role full access" ON proposals_proposalline;
            DROP POLICY IF EXISTS "Service role full access" ON proposals_proposalcalculationlog;
        EXCEPTION
            WHEN undefined_object THEN
                -- Policy doesn't exist, that's fine
                NULL;
        END $$;

        -- Create policies
        CREATE POLICY "Service role full access" ON django_migrations FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON django_content_type FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON django_admin_log FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON django_session FOR ALL USING (true);

        CREATE POLICY "Service role full access" ON auth_permission FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON auth_group FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON auth_group_permissions FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON auth_user FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON auth_user_groups FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON auth_user_user_permissions FOR ALL USING (true);

        CREATE POLICY "Service role full access" ON documents_document FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_auditlog FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_extractionresult FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_adminactionaudit FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_batch FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_batchdocument FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_betriebskennzahltemplate FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_extractionfailurepattern FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_holzartkennzahl FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_individuellebetriebskennzahl FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_komplexitaetkennzahl FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_materiallisteposition FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_oberflächenbearbeitungkennzahl FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_patternreviewsession FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_patternfixproposal FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_saisonalemarge FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_calculationexplanation FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_calculationfactor FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON documents_userprojectbenchmark FOR ALL USING (true);

        CREATE POLICY "Service role full access" ON extraction_extractionconfig FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON extraction_materialextraction FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON extraction_extractedentity FOR ALL USING (true);

        CREATE POLICY "Service role full access" ON proposals_proposal FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON proposals_proposaltemplate FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON proposals_proposalline FOR ALL USING (true);
        CREATE POLICY "Service role full access" ON proposals_proposalcalculationlog FOR ALL USING (true);
    """)


def disable_rls_if_supabase(apps, schema_editor):
    """Reverse migration: disable RLS"""
    db_name = schema_editor.connection.settings_dict.get('NAME', '')

    if db_name.startswith('test_'):
        print("⏭️  Skipping RLS reverse migration for test database")
        return

    print("🔄 Disabling RLS security (reverse migration)")

    schema_editor.execute("""
        -- Disable RLS on all tables
        ALTER TABLE IF EXISTS django_migrations DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS django_content_type DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS django_admin_log DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS django_session DISABLE ROW LEVEL SECURITY;

        ALTER TABLE IF EXISTS auth_permission DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_group DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_group_permissions DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_user DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_user_groups DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS auth_user_user_permissions DISABLE ROW LEVEL SECURITY;

        ALTER TABLE IF EXISTS documents_document DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_auditlog DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_extractionresult DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_adminactionaudit DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_batch DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_batchdocument DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_betriebskennzahltemplate DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_extractionfailurepattern DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_holzartkennzahl DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_individuellebetriebskennzahl DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_komplexitaetkennzahl DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_materiallisteposition DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_oberflächenbearbeitungkennzahl DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_patternreviewsession DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_patternfixproposal DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_saisonalemarge DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_calculationexplanation DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_calculationfactor DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS documents_userprojectbenchmark DISABLE ROW LEVEL SECURITY;

        ALTER TABLE IF EXISTS extraction_extractionconfig DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS extraction_materialextraction DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS extraction_extractedentity DISABLE ROW LEVEL SECURITY;

        ALTER TABLE IF EXISTS proposals_proposal DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS proposals_proposaltemplate DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS proposals_proposalline DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS proposals_proposalcalculationlog DISABLE ROW LEVEL SECURITY;
    """)


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_calculationexplanation_calculationfactor_and_more'),
        ('extraction', '0001_initial'),
        ('proposals', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            enable_rls_if_supabase,
            reverse_code=disable_rls_if_supabase,
        ),
    ]
