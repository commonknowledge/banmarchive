# Generated by Django 3.2.25 on 2025-03-02 20:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website_news', '0004_websitenewsindexpage_hero_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='websitenewssearch',
            name='copy',
        ),
        migrations.RemoveField(
            model_name='websitenewssearch',
            name='hero_image',
        ),
    ]
