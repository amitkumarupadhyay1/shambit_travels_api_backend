# Generated manually for Phase 1: Hotel Tier Redesign

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("packages", "0006_package_featured_image"),
    ]

    operations = [
        # Add new pricing fields to HotelTier
        migrations.AddField(
            model_name="hoteltier",
            name="base_price_per_night",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=2,
                help_text="Base price per room per night (weekday rate in INR)",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="hoteltier",
            name="weekend_multiplier",
            field=models.DecimalField(
                decimal_places=2,
                default=1.3,
                help_text="Weekend price multiplier (e.g., 1.3 = 30% increase for Fri-Sun)",
                max_digits=4,
            ),
        ),
        migrations.AddField(
            model_name="hoteltier",
            name="max_occupancy_per_room",
            field=models.IntegerField(
                default=2,
                help_text="Maximum number of people per room",
            ),
        ),
        migrations.AddField(
            model_name="hoteltier",
            name="room_types",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Available room types with prices: {"single": 1500, "double": 1700, "family": 2500}',
            ),
        ),
        migrations.AddField(
            model_name="hoteltier",
            name="amenities",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of included amenities: ["WiFi", "Breakfast", "AC", "Pool"]',
            ),
        ),
        # Update price_multiplier help text to mark as deprecated
        migrations.AlterField(
            model_name="hoteltier",
            name="price_multiplier",
            field=models.DecimalField(
                db_index=True,
                decimal_places=2,
                default=1.0,
                help_text="DEPRECATED: Use base_price_per_night instead. Kept for backward compatibility.",
                max_digits=4,
            ),
        ),
        # Add index for new base_price_per_night field
        migrations.AddIndex(
            model_name="hoteltier",
            index=models.Index(
                fields=["base_price_per_night"], name="packages_ho_base_pr_idx"
            ),
        ),
    ]
