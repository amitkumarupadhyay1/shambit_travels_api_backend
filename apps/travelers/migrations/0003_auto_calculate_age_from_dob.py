# Generated migration to make date_of_birth required and calculate age automatically

from django.db import migrations, models
from datetime import date


def set_default_dob_for_existing(apps, schema_editor):
    """Set default DOB for existing travelers based on their age"""
    Traveler = apps.get_model("travelers", "Traveler")
    today = date.today()

    for traveler in Traveler.objects.filter(date_of_birth__isnull=True):
        # Calculate approximate DOB from age
        if traveler.age:
            birth_year = today.year - traveler.age
            traveler.date_of_birth = date(birth_year, 1, 1)
            traveler.save()


class Migration(migrations.Migration):

    dependencies = [
        ("travelers", "0002_remove_traveler_passport_number_and_more"),
    ]

    operations = [
        # First, populate date_of_birth for existing records
        migrations.RunPython(set_default_dob_for_existing, migrations.RunPython.noop),
        # Then make date_of_birth required
        migrations.AlterField(
            model_name="traveler",
            name="date_of_birth",
            field=models.DateField(
                help_text="Date of birth (age will be calculated from this)"
            ),
        ),
        # Remove the age field (it's now a property)
        migrations.RemoveField(
            model_name="traveler",
            name="age",
        ),
    ]
