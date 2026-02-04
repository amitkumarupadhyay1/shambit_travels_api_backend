from django.core.management.base import BaseCommand
from seo.models import SEOData
from seo.services.seo_service import SEOService
from seo.utils import SEOAnalyzer


class Command(BaseCommand):
    help = "Perform SEO audit and generate report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--content-type",
            type=str,
            help="Audit specific content type (e.g., articles.article)",
        )
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed analysis for each SEO entry",
        )
        parser.add_argument(
            "--export", type=str, help="Export report to file (CSV format)"
        )

    def handle(self, *args, **options):
        content_type = options.get("content_type")
        detailed = options["detailed"]
        export_file = options.get("export")

        self.stdout.write(self.style.SUCCESS("Starting SEO Audit..."))

        # Get SEO health check
        health_report = SEOService.seo_health_check()

        # Display summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SEO AUDIT SUMMARY")
        self.stdout.write("=" * 50)

        self.stdout.write(f"Total SEO entries: {health_report['total_checked']}")
        self.stdout.write(
            f"Good SEO: {health_report['good_count']} ({health_report['health_percentage']:.1f}%)"
        )
        self.stdout.write(f"Warnings: {health_report['warning_count']}")
        self.stdout.write(f"Errors: {health_report['error_count']}")

        # Get overall stats
        stats = SEOService.get_seo_stats()

        self.stdout.write("\n" + "-" * 30)
        self.stdout.write("SEO COMPLETENESS")
        self.stdout.write("-" * 30)

        completeness = stats["completeness"]
        self.stdout.write(
            f"Complete basic SEO: {completeness['complete_basic_seo']} ({completeness['basic_seo_percentage']:.1f}%)"
        )
        self.stdout.write(
            f"With Open Graph: {completeness['with_open_graph']} ({completeness['og_percentage']:.1f}%)"
        )
        self.stdout.write(
            f"With Structured Data: {completeness['with_structured_data']} ({completeness['structured_data_percentage']:.1f}%)"
        )

        # Content type breakdown
        self.stdout.write("\n" + "-" * 30)
        self.stdout.write("BY CONTENT TYPE")
        self.stdout.write("-" * 30)

        for ct_data in stats["by_content_type"]:
            self.stdout.write(
                f"{ct_data['content_type__app_label']}.{ct_data['content_type__model']}: {ct_data['count']}"
            )

        # Top issues
        if health_report["top_issues"]:
            self.stdout.write("\n" + "-" * 30)
            self.stdout.write("TOP ISSUES")
            self.stdout.write("-" * 30)

            for issue in health_report["top_issues"][:5]:
                self.stdout.write(f"\n{issue['object']}:")
                for recommendation in issue["issues"][:3]:
                    self.stdout.write(f"  - {recommendation}")

        # Detailed analysis if requested
        if detailed:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("DETAILED ANALYSIS")
            self.stdout.write("=" * 50)

            queryset = SEOData.objects.all()
            if content_type:
                try:
                    app_label, model = content_type.split(".")
                    from django.contrib.contenttypes.models import ContentType

                    ct = ContentType.objects.get(app_label=app_label, model=model)
                    queryset = queryset.filter(content_type=ct)
                except (ValueError, ContentType.DoesNotExist):
                    self.stdout.write(
                        self.style.ERROR(f"Invalid content type: {content_type}")
                    )
                    return

            analyzer = SEOAnalyzer()

            for seo_data in queryset[:20]:  # Limit to 20 for readability
                analysis = analyzer.analyze_seo_data(seo_data)

                self.stdout.write(
                    f'\n{seo_data.content_object} ({analysis["overall_score"].upper()})'
                )
                self.stdout.write(
                    f'  Title: {analysis["title_length"]} chars ({analysis["title_score"]})'
                )
                self.stdout.write(
                    f'  Description: {analysis["description_length"]} chars ({analysis["description_score"]})'
                )
                self.stdout.write(
                    f'  Keywords: {analysis["keywords_count"]} ({analysis["keywords_score"]})'
                )
                self.stdout.write(
                    f'  Open Graph: {analysis["og_completeness"]*100:.0f}% complete'
                )

                if analysis["recommendations"]:
                    self.stdout.write("  Recommendations:")
                    for rec in analysis["recommendations"][:2]:
                        self.stdout.write(f"    - {rec}")

        # Export to CSV if requested
        if export_file:
            self.export_to_csv(export_file, stats, health_report)
            self.stdout.write(
                self.style.SUCCESS(f"\nReport exported to: {export_file}")
            )

        self.stdout.write(self.style.SUCCESS("\nSEO Audit Complete!"))

    def export_to_csv(self, filename, stats, health_report):
        """Export audit results to CSV file"""
        import csv
        from datetime import datetime

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow(
                ["SEO Audit Report", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            )
            writer.writerow([])

            # Summary
            writer.writerow(["Summary"])
            writer.writerow(["Total SEO Entries", health_report["total_checked"]])
            writer.writerow(["Good SEO", health_report["good_count"]])
            writer.writerow(["Warnings", health_report["warning_count"]])
            writer.writerow(["Errors", health_report["error_count"]])
            writer.writerow(
                ["Health Percentage", f"{health_report['health_percentage']:.1f}%"]
            )
            writer.writerow([])

            # Completeness
            writer.writerow(["Completeness"])
            completeness = stats["completeness"]
            writer.writerow(
                ["Complete Basic SEO", f"{completeness['basic_seo_percentage']:.1f}%"]
            )
            writer.writerow(
                ["With Open Graph", f"{completeness['og_percentage']:.1f}%"]
            )
            writer.writerow(
                [
                    "With Structured Data",
                    f"{completeness['structured_data_percentage']:.1f}%",
                ]
            )
            writer.writerow([])

            # By content type
            writer.writerow(["Content Type", "Count"])
            for ct_data in stats["by_content_type"]:
                writer.writerow(
                    [
                        f"{ct_data['content_type__app_label']}.{ct_data['content_type__model']}",
                        ct_data["count"],
                    ]
                )
