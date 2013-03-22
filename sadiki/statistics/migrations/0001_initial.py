# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StatisticsArchive'
        db.create_table('statistics_statisticsarchive', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('record_type', self.gf('django.db.models.fields.IntegerField')()),
            ('data', self.gf('django.db.models.fields.TextField')()),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('year', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('statistics', ['StatisticsArchive'])


    def backwards(self, orm):
        # Deleting model 'StatisticsArchive'
        db.delete_table('statistics_statisticsarchive')


    models = {
        'statistics.statisticsarchive': {
            'Meta': {'object_name': 'StatisticsArchive'},
            'data': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'record_type': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['statistics']