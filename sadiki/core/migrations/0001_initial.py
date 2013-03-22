# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EvidienceDocumentTemplate'
        db.create_table('core_evidiencedocumenttemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('format_tips', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('destination', self.gf('django.db.models.fields.IntegerField')()),
            ('regex', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('core', ['EvidienceDocumentTemplate'])

        # Adding model 'EvidienceDocument'
        db.create_table('core_evidiencedocument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.EvidienceDocumentTemplate'])),
            ('document_number', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('confirmed', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('core', ['EvidienceDocument'])

        # Adding model 'BenefitCategory'
        db.create_table('core_benefitcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('priority', self.gf('django.db.models.fields.IntegerField')()),
            ('immediately_distribution_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('core', ['BenefitCategory'])

        # Adding model 'Benefit'
        db.create_table('core_benefit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.BenefitCategory'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('has_time_limit', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('identifier', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('core', ['Benefit'])

        # Adding M2M table for field evidience_documents on 'Benefit'
        db.create_table('core_benefit_evidience_documents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('benefit', models.ForeignKey(orm['core.benefit'], null=False)),
            ('evidiencedocumenttemplate', models.ForeignKey(orm['core.evidiencedocumenttemplate'], null=False))
        ))
        db.create_unique('core_benefit_evidience_documents', ['benefit_id', 'evidiencedocumenttemplate_id'])

        # Adding M2M table for field sadik_related on 'Benefit'
        db.create_table('core_benefit_sadik_related', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('benefit', models.ForeignKey(orm['core.benefit'], null=False)),
            ('sadik', models.ForeignKey(orm['core.sadik'], null=False))
        ))
        db.create_unique('core_benefit_sadik_related', ['benefit_id', 'sadik_id'])

        # Adding model 'Address'
        db.create_table('core_address', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address_text', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('postindex', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('ocato', self.gf('django.db.models.fields.CharField')(max_length=11, null=True, blank=True)),
            ('block_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('building_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('extra_info', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('kladr', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('coords', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Address'])

        # Adding model 'Sadik'
        db.create_table('core_sadik', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Area'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('number', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('address', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Address'])),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('site', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('head_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('cast', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('tech_level', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('training_program', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('route_info', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('extended_info', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('active_registration', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('active_distribution', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('core', ['Sadik'])

        # Adding M2M table for field age_groups on 'Sadik'
        db.create_table('core_sadik_age_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sadik', models.ForeignKey(orm['core.sadik'], null=False)),
            ('agegroup', models.ForeignKey(orm['core.agegroup'], null=False))
        ))
        db.create_unique('core_sadik_age_groups', ['sadik_id', 'agegroup_id'])

        # Adding model 'AgeGroup'
        db.create_table('core_agegroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('from_age', self.gf('django.db.models.fields.IntegerField')()),
            ('from_date', self.gf('sadiki.core.fields.SplitDayMonthField')(max_length=10)),
            ('to_age', self.gf('django.db.models.fields.IntegerField')()),
            ('to_date', self.gf('sadiki.core.fields.SplitDayMonthField')(max_length=10)),
            ('next_age_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.AgeGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('core', ['AgeGroup'])

        # Adding model 'SadikGroup'
        db.create_table('core_sadikgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('age_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.AgeGroup'], null=True, blank=True)),
            ('other_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('cast', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sadik', self.gf('django.db.models.fields.related.ForeignKey')(related_name='groups', to=orm['core.Sadik'])),
            ('capacity', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('free_places', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('min_birth_date', self.gf('django.db.models.fields.DateField')()),
            ('max_birth_date', self.gf('django.db.models.fields.DateField')()),
            ('year', self.gf('django.db.models.fields.DateField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('core', ['SadikGroup'])

        # Adding model 'Vacancies'
        db.create_table('core_vacancies', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sadik_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.SadikGroup'])),
            ('distribution', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Distribution'], null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal('core', ['Vacancies'])

        # Adding model 'Distribution'
        db.create_table('core_distribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('init_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('start_datetime', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('end_datetime', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('year', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('core', ['Distribution'])

        # Adding model 'Profile'
        db.create_table('core_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Area'], null=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('patronymic', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('email_verified', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('mobile_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Profile'])

        # Adding M2M table for field sadiks on 'Profile'
        db.create_table('core_profile_sadiks', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('profile', models.ForeignKey(orm['core.profile'], null=False)),
            ('sadik', models.ForeignKey(orm['core.sadik'], null=False))
        ))
        db.create_unique('core_profile_sadiks', ['profile_id', 'sadik_id'])

        # Adding model 'Requestion'
        db.create_table('core_requestion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('admission_date', self.gf('sadiki.core.fields.YearChoiceField')(null=True, blank=True)),
            ('requestion_number', self.gf('django.db.models.fields.CharField')(max_length=23, null=True, blank=True)),
            ('distributed_in_vacancy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Vacancies'], null=True, blank=True)),
            ('agent_type', self.gf('django.db.models.fields.IntegerField')()),
            ('birth_date', self.gf('django.db.models.fields.DateField')()),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('patronymic', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('sex', self.gf('django.db.models.fields.CharField')(max_length=1, null=True)),
            ('cast', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=3, null=True)),
            ('registration_datetime', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('number_in_old_list', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('benefit_category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.BenefitCategory'], null=True)),
            ('profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Profile'])),
            ('address', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Address'], null=True)),
            ('status_change_datetime', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('distribute_in_any_sadik', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('core', ['Requestion'])

        # Adding M2M table for field areas on 'Requestion'
        db.create_table('core_requestion_areas', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('requestion', models.ForeignKey(orm['core.requestion'], null=False)),
            ('area', models.ForeignKey(orm['core.area'], null=False))
        ))
        db.create_unique('core_requestion_areas', ['requestion_id', 'area_id'])

        # Adding M2M table for field benefits on 'Requestion'
        db.create_table('core_requestion_benefits', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('requestion', models.ForeignKey(orm['core.requestion'], null=False)),
            ('benefit', models.ForeignKey(orm['core.benefit'], null=False))
        ))
        db.create_unique('core_requestion_benefits', ['requestion_id', 'benefit_id'])

        # Adding M2M table for field pref_sadiks on 'Requestion'
        db.create_table('core_requestion_pref_sadiks', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('requestion', models.ForeignKey(orm['core.requestion'], null=False)),
            ('sadik', models.ForeignKey(orm['core.sadik'], null=False))
        ))
        db.create_unique('core_requestion_pref_sadiks', ['requestion_id', 'sadik_id'])

        # Adding model 'Area'
        db.create_table('core_area', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('ocato', self.gf('django.db.models.fields.CharField')(max_length=11)),
            ('address', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Address'])),
            ('left_bottom', self.gf('django.db.models.fields.CharField')(default='180,90', max_length=255, blank=True)),
            ('right_top', self.gf('django.db.models.fields.CharField')(default='0,0', max_length=255, blank=True)),
        ))
        db.send_create_signal('core', ['Area'])


    def backwards(self, orm):
        # Deleting model 'EvidienceDocumentTemplate'
        db.delete_table('core_evidiencedocumenttemplate')

        # Deleting model 'EvidienceDocument'
        db.delete_table('core_evidiencedocument')

        # Deleting model 'BenefitCategory'
        db.delete_table('core_benefitcategory')

        # Deleting model 'Benefit'
        db.delete_table('core_benefit')

        # Removing M2M table for field evidience_documents on 'Benefit'
        db.delete_table('core_benefit_evidience_documents')

        # Removing M2M table for field sadik_related on 'Benefit'
        db.delete_table('core_benefit_sadik_related')

        # Deleting model 'Address'
        db.delete_table('core_address')

        # Deleting model 'Sadik'
        db.delete_table('core_sadik')

        # Removing M2M table for field age_groups on 'Sadik'
        db.delete_table('core_sadik_age_groups')

        # Deleting model 'AgeGroup'
        db.delete_table('core_agegroup')

        # Deleting model 'SadikGroup'
        db.delete_table('core_sadikgroup')

        # Deleting model 'Vacancies'
        db.delete_table('core_vacancies')

        # Deleting model 'Distribution'
        db.delete_table('core_distribution')

        # Deleting model 'Profile'
        db.delete_table('core_profile')

        # Removing M2M table for field sadiks on 'Profile'
        db.delete_table('core_profile_sadiks')

        # Deleting model 'Requestion'
        db.delete_table('core_requestion')

        # Removing M2M table for field areas on 'Requestion'
        db.delete_table('core_requestion_areas')

        # Removing M2M table for field benefits on 'Requestion'
        db.delete_table('core_requestion_benefits')

        # Removing M2M table for field pref_sadiks on 'Requestion'
        db.delete_table('core_requestion_pref_sadiks')

        # Deleting model 'Area'
        db.delete_table('core_area')


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
            'address_text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'block_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'building_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'coords': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'extra_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kladr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ocato': ('django.db.models.fields.CharField', [], {'max_length': '11', 'null': 'True', 'blank': 'True'}),
            'postindex': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'left_bottom': ('django.db.models.fields.CharField', [], {'default': "'180,90'", 'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ocato': ('django.db.models.fields.CharField', [], {'max_length': '11'}),
            'right_top': ('django.db.models.fields.CharField', [], {'default': "'0,0'", 'max_length': '255', 'blank': 'True'})
        },
        'core.benefit': {
            'Meta': {'object_name': 'Benefit'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.BenefitCategory']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'evidience_documents': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.EvidienceDocumentTemplate']", 'symmetrical': 'False'}),
            'has_time_limit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sadik_related': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['core.Sadik']", 'null': 'True', 'blank': 'True'})
        },
        'core.benefitcategory': {
            'Meta': {'object_name': 'BenefitCategory'},
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.EvidienceDocumentTemplate']"})
        },
        'core.evidiencedocumenttemplate': {
            'Meta': {'object_name': 'EvidienceDocumentTemplate'},
            'destination': ('django.db.models.fields.IntegerField', [], {}),
            'format_tips': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'regex': ('django.db.models.fields.TextField', [], {})
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
        'core.requestion': {
            'Meta': {'object_name': 'Requestion'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Address']", 'null': 'True'}),
            'admission_date': ('sadiki.core.fields.YearChoiceField', [], {'null': 'True', 'blank': 'True'}),
            'agent_type': ('django.db.models.fields.IntegerField', [], {}),
            'areas': ('sadiki.core.fields.AreaChoiceField', [], {'to': "orm['core.Area']", 'symmetrical': 'False'}),
            'benefit_category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.BenefitCategory']", 'null': 'True'}),
            'benefits': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Benefit']", 'symmetrical': 'False', 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {}),
            'cast': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'distribute_in_any_sadik': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'distributed_in_vacancy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Vacancies']", 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'number_in_old_list': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'patronymic': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'pref_sadiks': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Sadik']", 'symmetrical': 'False'}),
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
            'cast': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
        }
    }

    complete_apps = ['core']
