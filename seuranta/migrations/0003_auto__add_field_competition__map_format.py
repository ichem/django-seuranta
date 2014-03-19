# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Competition._map_format'
        db.add_column(u'seuranta_competition', '_map_format',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=12),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Competition._map_format'
        db.delete_column(u'seuranta_competition', '_map_format')


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
            'Meta': {'ordering': "['-_utc_start_date']", 'object_name': 'Competition'},
            '_map_format': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            '_utc_end_date': ('django.db.models.fields.DateTimeField', [], {}),
            '_utc_start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'calibration_string': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 3, 7, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'map_height': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'map_width': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Untitled'", 'max_length': '52'}),
            'publication_policy': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '8'}),
            'publisher': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitions'", 'to': u"orm['auth.User']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 3, 6, 0, 0)'}),
            'tile_url_template': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'timezone': ('timezone_field.fields.TimeZoneField', [], {'default': "'UTC'"}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'FNz5Pmh_ROOcqeTl8FNeKw'", 'unique': 'True', 'max_length': '36'})
        },
        u'seuranta.competitor': {
            'Meta': {'ordering': "['competition', 'start_time', 'name']", 'object_name': 'Competitor'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitors'", 'to': u"orm['seuranta.Competition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '52'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '52'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitors'", 'to': u"orm['seuranta.Tracker']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'lHTo8WJkRfqhcj3OMFASrA'", 'unique': 'True', 'max_length': '36'})
        },
        u'seuranta.routesection': {
            'Meta': {'ordering': "['-last_update']", 'object_name': 'RouteSection'},
            '_east': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            '_end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_north': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            '_south': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            '_start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_west': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'competitor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'route_sections'", 'to': u"orm['seuranta.Competitor']"}),
            'encoded_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'seuranta.tracker': {
            'Meta': {'ordering': "['-creation_date']", 'object_name': 'Tracker'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'handle': ('django.db.models.fields.CharField', [], {'max_length': '52', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pref_name': ('django.db.models.fields.CharField', [], {'max_length': '52', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'mqmFB8S-SIqMRbQVx99bDQ'", 'unique': 'True', 'max_length': '36'})
        }
    }

    complete_apps = ['seuranta']