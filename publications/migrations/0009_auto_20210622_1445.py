# Generated by Django 3.2.3 on 2021-06-22 14:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_articlepage'),
        ('publications', '0008_auto_20210610_1534'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='publication',
            name='introduction_author',
        ),
        migrations.RemoveField(
            model_name='publication',
            name='introduction_content',
        ),
        migrations.RemoveField(
            model_name='publication',
            name='introduction_date',
        ),
        migrations.AddField(
            model_name='publication',
            name='introduction_article',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.articlepage'),
        ),
    ]
