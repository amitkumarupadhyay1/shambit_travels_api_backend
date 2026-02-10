# Generated migration for Experience model enhancements
# Phase 1: Critical Backend Fixes

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("packages", "0002_alter_experience_options_alter_hoteltier_options_and_more"),
        ("cities", "0003_alter_city_hero_image"),
        ("media_library", "0002_alter_media_options"),
    ]

    operations = [
        # Add is_active field
        migrations.AddField(
            model_name="experience",
            name="is_active",
            field=models.BooleanField(db_index=True, default=True),
        ),
        # Add featured_image field
        migrations.AddField(
            model_name="experience",
            name="featured_image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="experiences",
                to="media_library.media",
            ),
        ),
        # Add duration_hours field
        migrations.AddField(
            model_name="experience",
            name="duration_hours",
            field=models.DecimalField(
                decimal_places=2,
                default=2.5,
                help_text="Duration in hours",
                max_digits=4,
            ),
        ),
        # Add max_participants field
        migrations.AddField(
            model_name="experience",
            name="max_participants",
            field=models.IntegerField(
                default=15, help_text="Maximum number of participants"
            ),
        ),
        # Add difficulty_level field
        migrations.AddField(
            model_name="experience",
            name="difficulty_level",
            field=models.CharField(
                choices=[
                    ("EASY", "Easy"),
                    ("MODERATE", "Moderate"),
                    ("HARD", "Hard"),
                ],
                db_index=True,
                default="EASY",
                max_length=20,
            ),
        ),
        # Add category field
        migrations.AddField(
            model_name="experience",
            name="category",
            field=models.CharField(
                choices=[
                    ("CULTURAL", "Cultural"),
                    ("ADVENTURE", "Adventure"),
                    ("FOOD", "Food & Culinary"),
                    ("SPIRITUAL", "Spiritual"),
                    ("NATURE", "Nature & Wildlife"),
                    ("ENTERTAINMENT", "Entertainment"),
                    ("EDUCATIONAL", "Educational"),
                ],
                db_index=True,
                default="CULTURAL",
                max_length=50,
            ),
        ),
        # Add city field
        migrations.AddField(
            model_name="experience",
            name="city",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="experiences",
                to="cities.city",
            ),
        ),
        # Add updated_at field
        migrations.AddField(
            model_name="experience",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        # Add new indexes
        migrations.AddIndex(
            model_name="experience",
            index=models.Index(
                fields=["category", "is_active"], name="packages_ex_categor_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="experience",
            index=models.Index(
                fields=["city", "is_active"], name="packages_ex_city_is_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="experience",
            index=models.Index(
                fields=["is_active", "created_at"], name="packages_ex_is_acti_idx"
            ),
        ),
    ]
