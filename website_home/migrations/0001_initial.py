# Generated by Django 3.2.25 on 2025-02-11 10:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0066_collection_management_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebsiteHomePage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('subtitle', models.CharField(blank=True, default='What is the Barry Amiel & Norman Melburn trust?', max_length=200)),
                ('copy', models.TextField(default='The Trust was founded in 1980 by Norman Melburn and named for his friend and fellow Marxist, the lawyer Barry Amiel. Since Norman Melburn’s death in 1991, both men have been commemorated in the name of the Trust.\nThe general objectives of the Trust are to advance public education, learning and knowledge in all aspects of the philosophy of Marxism, the history of socialism, and the working class movement. The Trust, as well as initiating activity or research in pursuit of these objects, is open to applications for funding.\nThe Trust will give financial assistance to bodies or individuals for projects which it considers fall within the scope of the Trust’s remit.')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
