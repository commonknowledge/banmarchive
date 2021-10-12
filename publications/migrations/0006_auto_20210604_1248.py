# Generated by Django 3.2.3 on 2021-06-04 12:48

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.contrib.taggit


class Migration(migrations.Migration):

    dependencies = [
        ('wagtaildocs', '0012_uploadeddocument'),
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('publications', '0005_article_intro_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(blank=True, help_text='A comma-separated list of tags.', through='publications.PageTag', to='taggit.Tag', verbose_name='Keywords'),
        ),
        migrations.AlterField(
            model_name='multiarticleissue',
            name='issue_cover',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtaildocs.document'),
        ),
    ]