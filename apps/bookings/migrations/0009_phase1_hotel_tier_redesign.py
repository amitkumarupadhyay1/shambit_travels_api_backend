# Generated manually for Phase 1: Hotel Tier Redesign

from datetime import timedelta
from django.db import migrations, models


def set_default_dates(apps, schema_editor):
    """
    Data migration: Set default values for new date fields based on existing booking_date
    """
    Booking = apps.get_model("bookings", "Booking")
    for booking in Booking.objects.all():
        if booking.booking_date and not booking.booking_start_date:
            booking.booking_start_date = booking.booking_date
            booking.booking_end_date = booking.booking_date + timedelta(days=1)
            booking.num_nights = 1
            booking.save(
                update_fields=["booking_start_date", "booking_end_date", "num_nights"]
            )


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0008_add_total_amount_paid"),
    ]

    operations = [
        # Add new date fields
        migrations.AddField(
            model_name="booking",
            name="booking_start_date",
            field=models.DateField(
                blank=True,
                db_index=True,
                help_text="Trip start date",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="booking_end_date",
            field=models.DateField(
                blank=True,
                db_index=True,
                help_text="Trip end date",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="num_nights",
            field=models.IntegerField(
                default=1,
                help_text="Number of nights (auto-calculated from start/end dates)",
            ),
        ),
        # Add room allocation fields
        migrations.AddField(
            model_name="booking",
            name="num_rooms_required",
            field=models.IntegerField(
                default=1,
                help_text="Number of rooms booked",
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="room_allocation",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Room allocation details: [{"room_type": "double", "occupants": [traveler_ids]}]',
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="room_preferences",
            field=models.TextField(
                blank=True,
                default="",
                help_text="User's room preferences or special requests for accommodation",
            ),
        ),
        # Add hotel cost breakdown fields
        migrations.AddField(
            model_name="booking",
            name="hotel_cost_per_night",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Hotel cost per night (all rooms combined)",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="total_hotel_cost",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Total hotel cost (all nights × all rooms)",
                max_digits=10,
                null=True,
            ),
        ),
        # Update booking_date help text to mark as deprecated
        migrations.AlterField(
            model_name="booking",
            name="booking_date",
            field=models.DateField(
                blank=True,
                db_index=True,
                help_text="DEPRECATED: Use booking_start_date instead. Kept for backward compatibility.",
                null=True,
            ),
        ),
        # Run data migration to populate new fields
        migrations.RunPython(set_default_dates, reverse_code=migrations.RunPython.noop),
    ]
