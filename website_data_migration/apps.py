from django.apps import AppConfig


class WebsiteDataMigrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "website_data_migration"

    def ready(self):
        import website_data_migration.signals
