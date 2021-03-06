# Generated by Django 3.2.3 on 2021-09-24 08:48

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.contrib.taggit
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('publications', '0012_auto_20210802_1736'),
    ]

    operations = [
        migrations.AddField(
            model_name='simpleissue',
            name='author_name',
            field=models.TextField(blank=True, default='', verbose_name='Author Names'),
        ),
        migrations.CreateModel(
            name='SimpleIssueTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_object', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='tagged_items', to='publications.simpleissue')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publications_simpleissuetag_items', to='taggit.tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='simpleissue',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(blank=True, help_text='A comma-separated list of tags.', through='publications.SimpleIssueTag', to='taggit.Tag', verbose_name='Keywords'),
        ),
    ]
