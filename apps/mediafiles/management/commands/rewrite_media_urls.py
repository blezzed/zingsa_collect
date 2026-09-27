from django.core.management.base import BaseCommand
from django.db import connection, transaction

from common.media_url_rewrite import public_media_base, rewrite_public_media_url


class Command(BaseCommand):
    help = (
        "Rewrite stored submission media URLs from direct MinIO (:9018 / old IP) "
        "to the public /minio/ proxy base."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report how many values would change without writing.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        base = public_media_base()
        if not base:
            self.stderr.write("AWS_S3_CUSTOM_DOMAIN is not configured; aborting.")
            return

        self.stdout.write(f"Public media base: {base}")
        updated_cells = 0
        scanned_tables = 0

        skip_tables = {
            "collect_form",
            "collect_form_version",
            "collect_project",
            "collect_project_member",
            "collect_organization",
            "collect_organization_member",
            "collect_submission_index",
            "collect_sync_log",
            "collect_feedback",
        }

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename LIKE 'collect\\_%'
                ORDER BY tablename
                """
            )
            tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            if table in skip_tables:
                continue

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    """,
                    [table],
                )
                columns = [
                    (name, data_type)
                    for name, data_type in cursor.fetchall()
                    if data_type in ("text", "character varying", "jsonb", "json")
                ]

            if not columns:
                continue

            scanned_tables += 1
            for col, data_type in columns:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        SELECT id, "{col}"::text
                        FROM "{table}"
                        WHERE "{col}"::text LIKE %s
                           OR "{col}"::text LIKE %s
                        """,
                        [
                            "%://172.30.5.24:9018/%",
                            "%://%:9018/zingsa-collect-media/%",
                        ],
                    )
                    rows = cursor.fetchall()

                for row_id, raw in rows:
                    if raw is None:
                        continue
                    rewritten = rewrite_public_media_url(raw)
                    if rewritten == raw:
                        continue

                    updated_cells += 1
                    if dry_run:
                        continue

                    with transaction.atomic():
                        with connection.cursor() as cursor:
                            if data_type in ("jsonb", "json"):
                                cursor.execute(
                                    f'UPDATE "{table}" SET "{col}" = %s::{data_type} WHERE id = %s',
                                    [rewritten, row_id],
                                )
                            else:
                                cursor.execute(
                                    f'UPDATE "{table}" SET "{col}" = %s WHERE id = %s',
                                    [rewritten, row_id],
                                )

        mode = "dry-run" if dry_run else "applied"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: scanned {scanned_tables} tables, updated {updated_cells} cells"
            )
        )
