# Generated by Django 3.2.25 on 2025-02-11 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website_about', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='websiteaboutindexpage',
            name='subtitle',
            field=models.CharField(default='About The Barry Amiel & Norman Melburn Trust', max_length=100),
        ),
    ]
