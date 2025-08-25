from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from django.db import connection

class Command(BaseCommand):
    help = 'Delete all data from the specified app and reset primary keys'

    def handle(self, *args, **options):
        app_name = 'system'  # Replace with your app's name
        self.stdout.write(f"Deleting data for app: {app_name}")

        with transaction.atomic():
            for model in apps.get_app_config(app_name).get_models():
                # Delete all data for each model
                model.objects.all().delete()

                # Reset the primary key after deletion for PostgreSQL, MySQL, or SQLite
                self.reset_primary_key(model)

        self.stdout.write(self.style.SUCCESS("Data deletion and primary key reset completed."))

    def reset_primary_key(self, model):
        """
        Reset the primary key for the given model after deletion.
        Handles PostgreSQL, MySQL, and SQLite.
        """
        table_name = model._meta.db_table

        # For PostgreSQL: Reset the sequence
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), 1, false);")

        # For MySQL: Reset the AUTO_INCREMENT
        elif connection.vendor == 'mysql':
            with connection.cursor() as cursor:
                cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")

        # For SQLite: Reset the primary key (auto-increment counter)
        elif connection.vendor == 'sqlite':
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
