# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Profile.social_auth_public'
        db.add_column('core_profile', 'social_auth_public',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Profile.social_auth_public'
        db.delete_column('core_profile', 'social_auth_public')


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
            'street': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'town': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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
            'bounds': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ocato': ('django.db.models.fields.CharField', [], {'max_length': '11'})
        },
        'core.benefit': {
            'Meta': {'object_name': 'Benefit'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.BenefitCategory']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'evidience_documents': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.EvidienceDocumentTemplate']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sadik_related': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['core.Sadik']", 'null': 'True', 'blank': 'True'})
        },
        'core.benefitcategory': {
            'Meta': {'object_name': 'BenefitCategory'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immediately_distribution_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'priority': ('django.db.models.fields.IntegerField', [], {})
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
        'core.evidiencedocument': {
            'Meta': {'object_name': 'EvidienceDocument'},
            'confirmed': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'document_number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'fake': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.EvidienceDocumentTemplate']"})
        },
        'core.evidiencedocumenttemplate': {
            'Meta': {'object_name': 'EvidienceDocumentTemplate'},
            'destination': ('django.db.models.fields.IntegerField', [], {}),
            'format_tips': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'regex': ('django.db.models.fields.TextField', [], {})
        },
        'core.preference': {
            'Meta': {'object_name': 'Preference'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'section': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'core.profile': {
            'Meta': {'object_name': 'Profile'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Area']", 'null': 'True'}),
            'email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'sadiks': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Sadik']", 'null': 'True', 'symmetrical': 'False'}),
            'skype': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'social_auth_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'core.requestion': {
            'Meta': {'ordering': "['-benefit_category__priority', 'registration_datetime', 'id']", 'object_name': 'Requestion'},
            'admission_date': ('sadiki.core.fields.YearChoiceField', [], {'null': 'True', 'blank': 'True'}),
            'areas': ('sadiki.core.fields.AreaChoiceField', [], {'to': "orm['core.Area']", 'symmetrical': 'False'}),
            'benefit_category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.BenefitCategory']", 'null': 'True'}),
            'benefits': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Benefit']", 'symmetrical': 'False', 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {}),
            'cast': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'decision_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'distribute_in_any_sadik': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'distributed_in_vacancy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Vacancies']", 'null': 'True', 'blank': 'True'}),
            'distribution_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'location_properties': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'number_in_old_list': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'pref_sadiks': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Sadik']", 'symmetrical': 'False'}),
            'previous_distributed_in_vacancy': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'previous_requestions'", 'null': 'True', 'to': "orm['core.Vacancies']"}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Profile']"}),
            'registration_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'requestion_number': ('django.db.models.fields.CharField', [], {'max_length': '23', 'null': 'True', 'blank': 'True'}),
            'sex': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '3', 'null': 'True'}),
            'status_change_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
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
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
        }
    }

    complete_apps = ['core']