# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Photo'
        db.create_table('administrator_photo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('administrator', ['Photo'])

        # Adding model 'ImportTask'
        db.create_table('administrator_importtask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('errors', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('total', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('fake', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('data_format', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('result_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('file_with_errors', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('administrator', ['ImportTask'])


    def backwards(self, orm):
        # Deleting model 'Photo'
        db.delete_table('administrator_photo')

        # Deleting model 'ImportTask'
        db.delete_table('administrator_importtask')


    models = {
        'administrator.importtask': {
            'Meta': {'object_name': 'ImportTask'},
            'data_format': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'fake': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'file_with_errors': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
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