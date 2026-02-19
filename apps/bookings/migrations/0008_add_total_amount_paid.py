# Generated migration for adding total_amount_paid field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0007_booking_traveler_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="total_amount_paid",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Total amount paid by customer (per_person_price × chargeable_travelers). This is the actual amount charged to the customer.",
                max_digits=12,
                null=True,
                db_index=True,
            ),
        ),
    ]
