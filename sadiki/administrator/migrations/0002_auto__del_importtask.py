# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'ImportTask'
        db.delete_table('administrator_importtask')


    def backwards(self, orm):
        # Adding model 'ImportTask'
        db.create_table('administrator_importtask', (
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('file_with_errors', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('total', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('errors', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('fake', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('source_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('result_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('data_format', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('administrator', ['ImportTask'])


    models = {
        'administrator.photo': {
            'Meta': {'object_name': 'Photo'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['administrator']