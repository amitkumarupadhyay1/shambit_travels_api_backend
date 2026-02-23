# Generated migration for vehicle allocation field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0010_add_booking_draft_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='vehicle_allocation',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Optimized vehicle allocation: [{"transport_option_id": 1, "count": 2}]',
            ),
        ),
    ]
