# Generated migration for vehicle optimization fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("packages", "0008_phase1_hotel_tier_redesign"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transportoption",
            name="base_price",
            field=models.DecimalField(
                db_index=True,
                decimal_places=2,
                help_text="DEPRECATED: Use base_price_per_day instead. Kept for backward compatibility.",
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name="transportoption",
            name="base_price_per_day",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=2,
                help_text="Base price per vehicle per day (24-hour period)",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="transportoption",
            name="passenger_capacity",
            field=models.IntegerField(
                default=4,
                help_text="Maximum passenger capacity per vehicle",
            ),
        ),
        migrations.AddField(
            model_name="transportoption",
            name="luggage_capacity",
            field=models.IntegerField(
                default=3,
                help_text="Maximum luggage pieces per vehicle",
            ),
        ),
        migrations.AddField(
            model_name="transportoption",
            name="is_active",
            field=models.BooleanField(
                db_index=True,
                default=True,
                help_text="Whether this vehicle type is available for booking",
            ),
        ),
        migrations.AddIndex(
            model_name="transportoption",
            index=models.Index(
                fields=["base_price_per_day"], name="packages_tra_base_pr_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="transportoption",
            index=models.Index(
                fields=["is_active", "base_price_per_day"],
                name="packages_tra_is_acti_idx",
            ),
        ),
    ]
