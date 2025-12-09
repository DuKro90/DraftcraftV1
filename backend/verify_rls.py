"""
Verify RLS is enabled on all Django tables in Supabase.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection

def verify_rls_enabled():
    """Check which tables have RLS enabled."""

    with connection.cursor() as cursor:
        # Query to check RLS status for all tables in public schema
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                rowsecurity as rls_enabled
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)

        tables = cursor.fetchall()

        print("\n" + "="*80)
        print("RLS STATUS FOR ALL PUBLIC TABLES")
        print("="*80 + "\n")

        enabled_count = 0
        disabled_count = 0

        for schema, table, rls_enabled in tables:
            status = "[ENABLED]" if rls_enabled else "[DISABLED]"
            print(f"{table:50s} {status}")

            if rls_enabled:
                enabled_count += 1
            else:
                disabled_count += 1

        print("\n" + "="*80)
        print(f"Summary: {enabled_count} tables with RLS ENABLED, {disabled_count} DISABLED")
        print("="*80 + "\n")

        # Also check policies
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                policyname,
                permissive,
                cmd
            FROM pg_policies
            WHERE schemaname = 'public'
            ORDER BY tablename, policyname;
        """)

        policies = cursor.fetchall()

        print("\n" + "="*80)
        print("RLS POLICIES DEFINED")
        print("="*80 + "\n")

        current_table = None
        for schema, table, policy_name, permissive, cmd in policies:
            if table != current_table:
                print(f"\n{table}:")
                current_table = table
            print(f"  - {policy_name} ({cmd})")

        print("\n" + "="*80)
        print(f"Total policies: {len(policies)}")
        print("="*80 + "\n")

        return enabled_count, disabled_count

if __name__ == "__main__":
    verify_rls_enabled()
