# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from seuranta.utils import make_random_code

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Competitor.quick_setup_code'
        db.add_column(u'seuranta_competitor', 'quick_setup_code',
                      self.gf('django.db.models.fields.CharField')(default=lambda: make_random_code(5), max_length=8, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Competitor.quick_setup_code'
        db.delete_column(u'seuranta_competitor', 'quick_setup_code')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'seuranta.competition': {
            'Meta': {'ordering': "['-opening_date']", 'object_name': 'Competition'},
            'calibration_string': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'closing_date': ('django.db.models.fields.DateTimeField', [], {}),
            'display_settings': ('django.db.models.fields.CharField', [], {'default': "'map'", 'max_length': '10'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'map': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'map_height': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'map_width': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Untitled'", 'max_length': '50'}),
            'opening_date': ('django.db.models.fields.DateTimeField', [], {}),
            'pref_tile_url_pattern': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'publication_policy': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '8'}),
            'publisher': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitions'", 'to': u"orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '21'}),
            'timezone': ('timezone_field.fields.TimeZoneField', [], {'default': "'UTC'"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '22', 'primary_key': 'True'})
        },
        u'seuranta.competitor': {
            'Meta': {'ordering': "['competition', 'starting_time', 'name']", 'unique_together': "(('tracker', 'competition'),)", 'object_name': 'Competitor'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitors'", 'to': u"orm['seuranta.Competition']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'quick_setup_code': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8', 'blank': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'starting_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.CharField', [], {'max_length': '22', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '22', 'primary_key': 'True'})
        },
        u'seuranta.routesection': {
            'Meta': {'ordering': "['-last_update']", 'object_name': 'RouteSection'},
            '_east': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            '_finish_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_north': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            '_south': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            '_start_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_west': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'competitor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'route_sections'", 'to': u"orm['seuranta.Competitor']"}),
            'encoded_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['seuranta']