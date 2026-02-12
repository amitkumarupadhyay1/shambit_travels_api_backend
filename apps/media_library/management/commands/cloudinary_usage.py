"""
Django management command to check Cloudinary usage
Usage: python manage.py cloudinary_usage
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from media_library.services.cloudinary_monitor import CloudinaryMonitor


class Command(BaseCommand):
    help = "Check Cloudinary usage and get recommendations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed usage statistics",
        )
        parser.add_argument(
            "--alerts-only",
            action="store_true",
            help="Show only alerts",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output in JSON format",
        )

    def handle(self, *args, **options):
        try:
            monitor = CloudinaryMonitor()

            if options["json"]:
                import json

                summary = monitor.get_summary()
                self.stdout.write(json.dumps(summary, indent=2))
                return

            if options["alerts_only"]:
                self._show_alerts_only(monitor)
                return

            if options["detailed"]:
                self._show_detailed(monitor)
            else:
                self._show_summary(monitor)

        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {str(e)}"))
            self.stdout.write("\nMake sure USE_CLOUDINARY=True in your .env file")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Unexpected error: {str(e)}"))

    def _show_summary(self, monitor):
        """Show summary view"""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("CLOUDINARY USAGE SUMMARY")
        self.stdout.write("=" * 70)

        summary = monitor.get_summary()
        stats = summary["stats"]

        if "error" in stats:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {stats['message']}"))
            return

        # Overall status
        overall_status = summary["overall_status"]
        status_icon = {
            "ok": "✅",
            "warning": "⚠️",
            "critical": "🔴",
        }.get(overall_status, "❓")

        self.stdout.write(f"\n{status_icon} Overall Status: {overall_status.upper()}")
        self.stdout.write(f"Timestamp: {stats['timestamp']}")

        # Storage
        self.stdout.write("\n📦 STORAGE:")
        storage = stats["storage"]
        self._print_resource(storage, "GB")

        # Bandwidth
        self.stdout.write("\n🌐 BANDWIDTH:")
        bandwidth = stats["bandwidth"]
        self._print_resource(bandwidth, "GB")

        # Transformations
        self.stdout.write("\n🔄 TRANSFORMATIONS:")
        transformations = stats["transformations"]
        self._print_resource(transformations, "count")

        # Credits
        self.stdout.write("\n💳 CREDITS:")
        credits = stats["credits"]
        self._print_resource(credits, "count")

        # Resources
        self.stdout.write(f"\n📁 Total Resources: {stats['resources']['count']}")

        # Alerts
        alerts = summary["alerts"]
        if alerts:
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write("⚠️  ALERTS")
            self.stdout.write("=" * 70)
            for alert in alerts:
                level_style = {
                    "warning": self.style.WARNING,
                    "critical": self.style.ERROR,
                    "error": self.style.ERROR,
                }.get(alert["level"], self.style.NOTICE)
                self.stdout.write(level_style(f"\n{alert['message']}"))

        # Recommendations
        recommendations = summary["recommendations"]
        if recommendations:
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write("💡 RECOMMENDATIONS")
            self.stdout.write("=" * 70)
            for rec in recommendations:
                self.stdout.write(f"\n{rec}")

        self.stdout.write("\n" + "=" * 70 + "\n")

    def _show_detailed(self, monitor):
        """Show detailed view"""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("CLOUDINARY DETAILED USAGE")
        self.stdout.write("=" * 70)

        stats = monitor.get_usage_stats()

        if "error" in stats:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {stats['message']}"))
            return

        # Storage details
        self.stdout.write("\n📦 STORAGE DETAILS:")
        storage = stats["storage"]
        self.stdout.write(
            f"   Used: {storage['used_gb']} GB ({storage['used_bytes']:,} bytes)"
        )
        self.stdout.write(f"   Limit: {storage['limit_gb']} GB")
        self.stdout.write(f"   Percentage: {storage['percentage']}%")
        self.stdout.write(f"   Status: {storage['status'].upper()}")
        if storage["alert"]:
            self.stdout.write(self.style.WARNING(f"   Alert: {storage['alert']}"))

        # Bandwidth details
        self.stdout.write("\n🌐 BANDWIDTH DETAILS:")
        bandwidth = stats["bandwidth"]
        self.stdout.write(
            f"   Used: {bandwidth['used_gb']} GB ({bandwidth['used_bytes']:,} bytes)"
        )
        self.stdout.write(f"   Limit: {bandwidth['limit_gb']} GB")
        self.stdout.write(f"   Percentage: {bandwidth['percentage']}%")
        self.stdout.write(f"   Status: {bandwidth['status'].upper()}")
        if bandwidth["alert"]:
            self.stdout.write(self.style.WARNING(f"   Alert: {bandwidth['alert']}"))

        # Transformations details
        self.stdout.write("\n🔄 TRANSFORMATIONS DETAILS:")
        transformations = stats["transformations"]
        self.stdout.write(f"   Used: {transformations['used']:,}")
        self.stdout.write(f"   Limit: {transformations['limit']:,}")
        self.stdout.write(f"   Percentage: {transformations['percentage']}%")
        self.stdout.write(f"   Status: {transformations['status'].upper()}")
        if transformations["alert"]:
            self.stdout.write(
                self.style.WARNING(f"   Alert: {transformations['alert']}")
            )

        # Credits details
        self.stdout.write("\n💳 CREDITS DETAILS:")
        credits = stats["credits"]
        self.stdout.write(f"   Used: {credits['used']}")
        self.stdout.write(f"   Limit: {credits['limit']}")
        self.stdout.write(f"   Percentage: {credits['percentage']}%")
        self.stdout.write(f"   Status: {credits['status'].upper()}")
        if credits["alert"]:
            self.stdout.write(self.style.WARNING(f"   Alert: {credits['alert']}"))

        # Resources
        self.stdout.write(f"\n📁 Total Resources: {stats['resources']['count']}")

        # Recommendations
        recommendations = monitor.get_recommendations()
        if recommendations:
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write("💡 RECOMMENDATIONS")
            self.stdout.write("=" * 70)
            for rec in recommendations:
                self.stdout.write(f"\n{rec}")

        self.stdout.write("\n" + "=" * 70 + "\n")

    def _show_alerts_only(self, monitor):
        """Show only alerts"""
        alerts = monitor.get_alerts()

        if not alerts:
            self.stdout.write(self.style.SUCCESS("\n✅ No alerts. Usage is healthy.\n"))
            return

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"⚠️  ACTIVE ALERTS ({len(alerts)})")
        self.stdout.write("=" * 70)

        for alert in alerts:
            level_style = {
                "warning": self.style.WARNING,
                "critical": self.style.ERROR,
                "error": self.style.ERROR,
            }.get(alert["level"], self.style.NOTICE)

            self.stdout.write(f"\n{alert['level'].upper()}: {alert['resource']}")
            self.stdout.write(level_style(f"  {alert['message']}"))
            if "percentage" in alert:
                self.stdout.write(f"  Usage: {alert['percentage']}%")

        self.stdout.write("\n" + "=" * 70 + "\n")

    def _print_resource(self, resource_data, unit):
        """Helper to print resource usage"""
        percentage = resource_data["percentage"]
        status = resource_data["status"]

        # Status icon
        status_icon = {
            "ok": "✅",
            "warning": "⚠️",
            "critical": "🔴",
        }.get(status, "❓")

        # Progress bar
        bar_length = 40
        filled = int((percentage / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        # Color based on status
        if status == "critical":
            bar_display = self.style.ERROR(bar)
        elif status == "warning":
            bar_display = self.style.WARNING(bar)
        else:
            bar_display = self.style.SUCCESS(bar)

        if unit == "GB":
            self.stdout.write(
                f"   {status_icon} {resource_data['used_gb']} / {resource_data['limit_gb']} GB"
            )
        else:
            self.stdout.write(
                f"   {status_icon} {resource_data['used']:,} / {resource_data['limit']:,}"
            )

        self.stdout.write(f"   {bar_display} {percentage}%")
