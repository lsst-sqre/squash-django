# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import json_field.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('ci_id', models.CharField(help_text='Jenkins job ID', max_length=16)),
                ('ci_name', models.CharField(help_text='Name of the Jenkins project,e.g. validate_drp', max_length=32)),
                ('ci_dataset', models.CharField(help_text='Name of the dataset, e.g cfht', max_length=16)),
                ('ci_label', models.CharField(help_text='Name of the platform, eg. centos-7', max_length=16)),
                ('date', models.DateTimeField(help_text='Datetime when job was registered', auto_now_add=True)),
                ('ci_url', models.URLField(help_text='Jenkins job URL')),
                ('status', models.SmallIntegerField(help_text='Job status, 0=OK, 1=Failed', default=0)),
                ('blobs', json_field.fields.JSONField(help_text='Data blobs produced by the job.', null=True, default=None, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('value', models.FloatField(help_text='Metric scalar measurement')),
                ('metadata', json_field.fields.JSONField(help_text='Measurement metadata', null=True, default=None, blank=True)),
                ('job', models.ForeignKey(to='api.Job', related_name='measurements')),
            ],
        ),
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('metric', models.CharField(help_text='Metric name', serialize=False, primary_key=True, max_length=16)),
                ('unit', models.CharField(help_text='Metric unit, astropy compatible string', null=True, blank=True, default='', max_length=16)),
                ('description', models.TextField(help_text='Metric description')),
                ('operator', models.CharField(help_text='Operator used to test measurementvalue against metric specification', default='<', max_length=2)),
                ('parameters', json_field.fields.JSONField(help_text='Parameters used to define the metric', null=True, default=None, blank=True)),
                ('specs', json_field.fields.JSONField(help_text='Array of metric specification', null=True, default=None, blank=True)),
                ('reference', json_field.fields.JSONField(help_text='Metric reference', null=True, default=None, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='VersionedPackage',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.SlugField(help_text='EUPS package name', max_length=64)),
                ('git_url', models.URLField(help_text='Git repo URL for package', max_length=128)),
                ('git_commit', models.CharField(help_text='SHA1 hash of the git commit', max_length=40)),
                ('git_branch', models.TextField(help_text='Resolved git branch that the commit resides on')),
                ('build_version', models.TextField(help_text='EUPS build version')),
                ('job', models.ForeignKey(to='api.Job', related_name='packages')),
            ],
        ),
        migrations.AddField(
            model_name='measurement',
            name='metric',
            field=models.ForeignKey(to='api.Metric'),
        ),
    ]
