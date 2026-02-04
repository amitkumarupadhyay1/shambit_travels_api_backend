from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from seo.services.seo_service import SEOService


class Command(BaseCommand):
    help = "Generate SEO data for objects missing it"

    def add_arguments(self, parser):
        parser.add_argument(
            "content_type",
            type=str,
            help="Content type in format app_label.model (e.g., articles.article)",
        )
        parser.add_argument(
            "--object-ids",
            nargs="+",
            type=int,
            help="Specific object IDs to generate SEO for",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without actually creating",
        )
        parser.add_argument(
            "--overwrite", action="store_true", help="Overwrite existing SEO data"
        )

    def handle(self, *args, **options):
        content_type = options["content_type"]
        object_ids = options.get("object_ids")
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        try:
            app_label, model = content_type.split(".")
            ct = ContentType.objects.get(app_label=app_label, model=model)
            model_class = ct.model_class()
        except (ValueError, ContentType.DoesNotExist):
            self.stdout.write(self.style.ERROR(f"Invalid content type: {content_type}"))
            return

        # Get objects to process
        if object_ids:
            objects = model_class.objects.filter(id__in=object_ids)
        else:
            # Find objects missing SEO data
            missing_data = SEOService.find_missing_seo_data(content_type)
            missing_ids = [obj["id"] for obj in missing_data["missing_objects"]]
            objects = model_class.objects.filter(id__in=missing_ids)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Would generate SEO data for {objects.count()} {model} objects"
                )
            )
            for obj in objects[:10]:  # Show first 10
                self.stdout.write(f"  - {obj}")
            if objects.count() > 10:
                self.stdout.write(f"  ... and {objects.count() - 10} more")
            return

        # Generate SEO data
        created_count = 0
        updated_count = 0
        error_count = 0

        for obj in objects:
            try:
                seo_data, created = SEOService.get_or_create_seo_data(
                    content_type=content_type,
                    object_id=obj.id,
                    defaults=SEOService._generate_seo_for_object(obj),
                )

                if created:
                    created_count += 1
                    self.stdout.write(f"Created SEO data for: {obj}")
                elif overwrite:
                    # Update existing
                    new_seo_data = SEOService._generate_seo_for_object(obj)
                    for key, value in new_seo_data.items():
                        setattr(seo_data, key, value)
                    seo_data.save()
                    updated_count += 1
                    self.stdout.write(f"Updated SEO data for: {obj}")
                else:
                    self.stdout.write(f"SEO data already exists for: {obj}")

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"Error processing {obj}: {str(e)}"))

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"SEO generation complete: {created_count} created, "
                f"{updated_count} updated, {error_count} errors"
            )
        )
