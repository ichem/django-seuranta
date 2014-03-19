# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tracker'
        db.create_table(u'seuranta_tracker', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(default='iW0ElqY7TBqT1YyFt9ShuQ', unique=True, max_length=36)),
            ('handle', self.gf('django.db.models.fields.CharField')(max_length=52, blank=True)),
            ('pref_name', self.gf('django.db.models.fields.CharField')(max_length=52, blank=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_seen', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'seuranta', ['Tracker'])

        # Adding model 'Competition'
        db.create_table(u'seuranta_competition', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(default='eP1XQ3TZTQmt6GMx3K0GCA', unique=True, max_length=36)),
            ('publisher', self.gf('django.db.models.fields.related.ForeignKey')(related_name='competitions', to=orm['auth.User'])),
            ('publication_policy', self.gf('django.db.models.fields.CharField')(default='public', max_length=8)),
            ('name', self.gf('django.db.models.fields.CharField')(default='Untitled', max_length=52)),
            ('tile_url_template', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('map', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('map_width', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('map_height', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('calibration_string', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 3, 6, 0, 0))),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 3, 7, 0, 0))),
            ('timezone', self.gf('timezone_field.fields.TimeZoneField')(default='UTC')),
            ('_utc_start_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('_utc_end_date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'seuranta', ['Competition'])

        # Adding model 'Competitor'
        db.create_table(u'seuranta_competitor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(default='cUAD11CBRVaEeUHSmS05hg', unique=True, max_length=36)),
            ('competition', self.gf('django.db.models.fields.related.ForeignKey')(related_name='competitors', to=orm['seuranta.Competition'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=52)),
            ('shortname', self.gf('django.db.models.fields.CharField')(max_length=52)),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('tracker', self.gf('django.db.models.fields.related.ForeignKey')(related_name='competitors', to=orm['seuranta.Tracker'])),
        ))
        db.send_create_signal(u'seuranta', ['Competitor'])

        # Adding model 'RouteSection'
        db.create_table(u'seuranta_routesection', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('competitor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='route_sections', to=orm['seuranta.Competitor'])),
            ('encoded_data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('_start_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('_end_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('_north', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('_south', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('_east', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('_west', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'seuranta', ['RouteSection'])


    def backwards(self, orm):
        # Deleting model 'Tracker'
        db.delete_table(u'seuranta_tracker')

        # Deleting model 'Competition'
        db.delete_table(u'seuranta_competition')

        # Deleting model 'Competitor'
        db.delete_table(u'seuranta_competitor')

        # Deleting model 'RouteSection'
        db.delete_table(u'seuranta_routesection')


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
            '_utc_end_date': ('django.db.models.fields.DateTimeField', [], {}),
            '_utc_start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'calibration_string': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
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
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'AeM0VPu1Q6a9Wsg6fByBMw'", 'unique': 'True', 'max_length': '36'})
        },
        u'seuranta.competitor': {
            'Meta': {'ordering': "['competition', 'start_time', 'name']", 'object_name': 'Competitor'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitors'", 'to': u"orm['seuranta.Competition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '52'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '52'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'tracker': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitors'", 'to': u"orm['seuranta.Tracker']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'FeYgnZsuT8KpCOHrFhZ27Q'", 'unique': 'True', 'max_length': '36'})
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
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'aa7r_ockRI6T3Ll4zUkI2g'", 'unique': 'True', 'max_length': '36'})
        }
    }

    complete_apps = ['seuranta']