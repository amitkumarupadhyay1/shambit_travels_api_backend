# Generated migration for Railway deployment fix

from django.db import migrations, models
import cities.models


class Migration(migrations.Migration):

    dependencies = [
        ('cities', '0002_alter_city_created_at_alter_city_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='city',
            name='hero_image',
            field=models.ImageField(blank=True, null=True, upload_to=cities.models.city_image_upload_path),
        ),
    ]