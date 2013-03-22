# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Logger.distribution_type'
        db.add_column('logger_logger', 'distribution_type',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Logger.distribution_type'
        db.delete_column('logger_logger', 'distribution_type')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.address': {
            'Meta': {'object_name': 'Address'},
            'block_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'building_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'coords': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'extra_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kladr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ocato': ('django.db.models.fields.CharField', [], {'max_length': '11', 'null': 'True', 'blank': 'True'}),
            'postindex': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        'core.agegroup': {
            'Meta': {'ordering': "['from_age']", 'object_name': 'AgeGroup'},
            'from_age': ('django.db.models.fields.IntegerField', [], {}),
            'from_date': ('sadiki.core.fields.SplitDayMonthField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'next_age_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AgeGroup']", 'null': 'True', 'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'to_age': ('django.db.models.fields.IntegerField', [], {}),
            'to_date': ('sadiki.core.fields.SplitDayMonthField', [], {'max_length': '10'})
        },
        'core.area': {
            'Meta': {'object_name': 'Area'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Address']"}),
            'bounds': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ocato': ('django.db.models.fields.CharField', [], {'max_length': '11'})
        },
        'core.distribution': {
            'Meta': {'object_name': 'Distribution'},
            'end_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'init_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'year': ('django.db.models.fields.DateField', [], {})
        },
        'core.profile': {
            'Meta': {'object_name': 'Profile'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Area']", 'null': 'True'}),
            'email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'mobile_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'patronymic': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'sadiks': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Sadik']", 'null': 'True', 'symmetrical': 'False'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'core.sadik': {
            'Meta': {'ordering': "['number']", 'object_name': 'Sadik'},
            'active_distribution': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'active_registration': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Address']"}),
            'age_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.AgeGroup']", 'symmetrical': 'False'}),
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Area']"}),
            'cast': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'extended_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'head_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'route_info': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'tech_level': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'training_program': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'core.sadikgroup': {
            'Meta': {'ordering': "['-min_birth_date']", 'object_name': 'SadikGroup'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'age_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AgeGroup']", 'null': 'True', 'blank': 'True'}),
            'capacity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'cast': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'distributions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Distribution']", 'through': "orm['core.Vacancies']", 'symmetrical': 'False'}),
            'free_places': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_birth_date': ('django.db.models.fields.DateField', [], {}),
            'min_birth_date': ('django.db.models.fields.DateField', [], {}),
            'other_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sadik': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['core.Sadik']"}),
            'year': ('django.db.models.fields.DateField', [], {})
        },
        'core.vacancies': {
            'Meta': {'object_name': 'Vacancies'},
            'distribution': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Distribution']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sadik_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.SadikGroup']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'logger.logger': {
            'Meta': {'object_name': 'Logger'},
            'action_flag': ('django.db.models.fields.IntegerField', [], {}),
            'added_pref_sadiks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'logger_added'", 'symmetrical': 'False', 'to': "orm['core.Sadik']"}),
            'age_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.AgeGroup']", 'symmetrical': 'False'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'distribution_type': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Profile']", 'null': 'True'}),
            'reason': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'removed_pref_sadiks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'logger_removed'", 'symmetrical': 'False', 'to': "orm['core.Sadik']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'vacancy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Vacancies']", 'null': 'True'})
        },
        'logger.loggermessage': {
            'Meta': {'ordering': "['-level']", 'object_name': 'LoggerMessage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'default': '40', 'db_index': 'True', 'blank': 'True'}),
            'logger': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logger.Logger']"}),
            'message': ('django.db.models.fields.TextField', [], {})
        },
        'logger.report': {
            'Meta': {'object_name': 'Report'},
            'age_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AgeGroup']", 'null': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'decision_type': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'from_date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_date': ('django.db.models.fields.DateField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['logger']