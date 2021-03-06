# Generated by Django 3.2.3 on 2021-06-22 14:45

from django.db import migrations, models
import django.db.models.deletion
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0062_comment_models_and_pagesubscription'),
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticlePage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('author', models.CharField(blank=True, default='', max_length=1024)),
                ('author_role', models.CharField(blank=True, default='', max_length=1024)),
                ('date', models.DateField(blank=True, null=True)),
                ('content', wagtail.core.fields.StreamField([('paragraph', wagtail.core.blocks.RichTextBlock()), ('pull_quote', wagtail.core.blocks.TextBlock()), ('side_image', wagtail.images.blocks.ImageChooserBlock())])),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
