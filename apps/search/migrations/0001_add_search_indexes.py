"""
Add GIN indexes for PostgreSQL full-text search
This migration creates indexes on searchable fields to improve search performance
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("packages", "0006_package_featured_image"),
        ("cities", "0003_alter_city_hero_image"),
        ("articles", "0003_article_featured_image"),
    ]

    operations = [
        # Add GIN indexes for fast full-text search
        migrations.RunSQL(
            sql="""
            -- Packages search index
            CREATE INDEX IF NOT EXISTS packages_package_search_idx 
            ON packages_package 
            USING GIN (to_tsvector('english', 
                COALESCE(name, '') || ' ' || 
                COALESCE(description, '')
            ));
            
            -- Cities search index
            CREATE INDEX IF NOT EXISTS cities_city_search_idx 
            ON cities_city 
            USING GIN (to_tsvector('english', 
                COALESCE(name, '') || ' ' || 
                COALESCE(description, '')
            ));
            
            -- Articles search index
            CREATE INDEX IF NOT EXISTS articles_article_search_idx 
            ON articles_article 
            USING GIN (to_tsvector('english', 
                COALESCE(title, '') || ' ' || 
                COALESCE(content, '') || ' ' || 
                COALESCE(author, '')
            ));
            
            -- Experiences search index
            CREATE INDEX IF NOT EXISTS packages_experience_search_idx 
            ON packages_experience 
            USING GIN (to_tsvector('english', 
                COALESCE(name, '') || ' ' || 
                COALESCE(description, '')
            ));
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS packages_package_search_idx;
            DROP INDEX IF EXISTS cities_city_search_idx;
            DROP INDEX IF EXISTS articles_article_search_idx;
            DROP INDEX IF EXISTS packages_experience_search_idx;
            """,
        ),
    ]
