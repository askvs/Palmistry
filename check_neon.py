
import os
import psycopg

url = os.getenv("NEON_CHECK_URL")
try:
    with psycopg.connect(url, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)

            tables = [row[0] for row in cur.fetchall()]

            print("Neon connection: SUCCESS")
            print("Tables found:", len(tables))

            for table in tables:
                print("-", table)

            if "alembic_version" in tables:
                cur.execute("SELECT version_num FROM alembic_version")
                print("Applied revision:", cur.fetchone())
            else:
                print("Alembic version table: NOT FOUND")

except Exception as exc:
    print("Check failed:", type(exc).__name__)
    print("Details:", str(exc))
