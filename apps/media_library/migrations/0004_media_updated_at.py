from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("media_library", "0003_alter_media_content_type_alter_media_object_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="media",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
