"""
Management command to set up default tax and pricing rules.
Usage: python manage.py setup_tax_rules
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from pricing_engine.models import PricingRule


class Command(BaseCommand):
    help = "Set up default tax and pricing rules for the platform"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing tax rules and create fresh ones",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("🏛️  SETTING UP TAX & PRICING RULES"))
        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))

        # Reset if requested
        if options["reset"]:
            self.stdout.write(self.style.WARNING("⚠️  Resetting existing tax rules..."))
            deleted_count = PricingRule.objects.filter(
                name__in=["GST (18%)", "Service Charge", "Platform Fee"]
            ).delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f"✅ Deleted {deleted_count} existing rules\n")
            )

        # 1. GST (Goods and Services Tax) - 18%
        gst_rule, created = PricingRule.objects.get_or_create(
            name="GST (18%)",
            defaults={
                "rule_type": "MARKUP",
                "value": 18.00,
                "is_percentage": True,
                "target_package": None,  # Apply to all packages
                "active_from": timezone.now(),
                "active_to": None,  # No expiry
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS("✅ Created: GST (18%) - Goods and Services Tax")
            )
            self.stdout.write("   Type: Markup (Percentage)")
            self.stdout.write("   Rate: 18%")
            self.stdout.write("   Applies to: All packages")
            self.stdout.write("   Status: Active\n")
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  GST (18%) rule already exists - skipped\n")
            )

        # 2. Service Charge - Fixed ₹500
        service_charge, created = PricingRule.objects.get_or_create(
            name="Service Charge",
            defaults={
                "rule_type": "MARKUP",
                "value": 500.00,
                "is_percentage": False,
                "target_package": None,
                "active_from": timezone.now(),
                "active_to": None,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS("✅ Created: Service Charge - Platform service fee")
            )
            self.stdout.write("   Type: Markup (Fixed Amount)")
            self.stdout.write("   Amount: ₹500")
            self.stdout.write("   Applies to: All packages")
            self.stdout.write("   Status: Active\n")
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  Service Charge rule already exists - skipped\n")
            )

        # 3. Platform Fee - 2% (Optional, disabled by default)
        platform_fee, created = PricingRule.objects.get_or_create(
            name="Platform Fee",
            defaults={
                "rule_type": "MARKUP",
                "value": 2.00,
                "is_percentage": True,
                "target_package": None,
                "active_from": timezone.now(),
                "active_to": None,
                "is_active": False,  # Disabled by default
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Created: Platform Fee - Additional platform charge (DISABLED)"
                )
            )
            self.stdout.write("   Type: Markup (Percentage)")
            self.stdout.write("   Rate: 2%")
            self.stdout.write("   Applies to: All packages")
            self.stdout.write("   Status: Inactive (can be enabled from admin)\n")
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  Platform Fee rule already exists - skipped\n")
            )

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("📊 SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        total_rules = PricingRule.objects.count()
        active_rules = PricingRule.objects.filter(is_active=True).count()
        inactive_rules = total_rules - active_rules

        self.stdout.write(f"\nTotal Pricing Rules: {total_rules}")
        self.stdout.write(f"Active Rules: {active_rules}")
        self.stdout.write(f"Inactive Rules: {inactive_rules}")

        self.stdout.write(self.style.SUCCESS("\n✅ Tax rules setup complete!"))
        self.stdout.write(
            self.style.SUCCESS("\n💡 You can manage these rules from Django Admin:")
        )
        self.stdout.write("   → /admin/pricing_engine/pricingrule/")
        self.stdout.write("\n💡 To modify tax rates when government changes them:")
        self.stdout.write("   1. Go to Django Admin")
        self.stdout.write("   2. Navigate to Pricing Rules")
        self.stdout.write("   3. Edit the GST rule and change the value")
        self.stdout.write("   4. Save - changes apply immediately!\n")
        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))
