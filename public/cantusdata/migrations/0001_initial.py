# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name=b'Manuscript',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                (b'name', models.CharField(max_length=255, null=True, blank=True)),
                (b'siglum', models.CharField(max_length=255, null=True, blank=True)),
                (b'date', models.CharField(max_length=50, null=True, blank=True)),
                (b'provenance', models.CharField(max_length=100, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name=b'Chant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                (b'marg', models.CharField(max_length=255, null=True, blank=True)),
                (b'folio', models.CharField(max_length=50, null=True, blank=True)),
                (b'sequence', models.PositiveSmallIntegerField()),
                (b'cantusID', models.CharField(max_length=50, null=True, blank=True)),
                (b'feast', models.CharField(max_length=255, null=True, blank=True)),
                (b'office', models.CharField(max_length=255, null=True, blank=True)),
                (b'genre', models.CharField(max_length=255, null=True, blank=True)),
                (b'litPosition', models.CharField(max_length=255, null=True, blank=True)),
                (b'mode', models.CharField(max_length=255, null=True, blank=True)),
                (b'differentia', models.CharField(max_length=255, null=True, blank=True)),
                (b'finalis', models.CharField(max_length=255, null=True, blank=True)),
                (b'incipit', models.TextField(null=True, blank=True)),
                (b'fullText', models.TextField(null=True, blank=True)),
                (b'concordances', models.CharField(max_length=255, null=True, blank=True)),
                (b'volpiano', models.CharField(max_length=255, null=True, blank=True)),
                (b'manuscript', models.ForeignKey(to=b'cantusdata.Manuscript', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
