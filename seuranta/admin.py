import pytz
from .models import Tracker, Competition, Competitor, RouteSection
from django.contrib import admin

from django.utils.timezone import utc, now

class PublisherAdmin(admin.ModelAdmin):
	def save_model(self, request, obj, form, change):
		if obj.publisher_id is None:
			obj.publisher = request.user
		obj.save()

	def queryset(self, request):
		qs = super(PublisherAdmin, self).queryset(request)
		if request.user.is_superuser:
			return qs
		return qs.filter(publisher=request.user)

	def has_add_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True

		if obj is None:
			return True
		else:
			return obj.publisher == request.user

	def has_change_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True

		if obj is None:
			return True
		else:
			return obj.publisher == request.user

	def has_delete_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True

		if obj is None:
			return True
		else:
			return obj.publisher == request.user

class CompetitorInlineAdmin(admin.TabularInline):
    model = Competitor
    raw_id_fields = ("tracker",)
    prepopulated_fields = {'shortname':('name',),}

class TrackerAdmin(PublisherAdmin):
    list_display = ('uuid', 'creation_date', 'get_competitor_list_tag', 'get_html_link_tag')

    class Media:
        js = {
            "//code.jquery.com/jquery-2.1.0.min.js",
            "//cdnjs.cloudflare.com/ajax/libs/jquery.qrcode/1.0/jquery.qrcode.min.js",
            "seuranta/admin/js/tracker.js",
        }

class CompetitionAdmin(PublisherAdmin):
    list_display = ('uuid', 'name', 'opening_date', 'closing_date', 'publication_policy')
    
    inlines = [
        CompetitorInlineAdmin,
    ]

    def save_model(self, request, obj, form, change):
        if obj.publisher_id is None:
            obj.publisher = request.user
        tz = obj.timezone
        if obj.opening_date is not None:
            obj.opening_date = utc.localize(tz.localize(obj.opening_date.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))
        
        if obj.closing_date is not None:
            obj.closing_date = utc.localize(tz.localize(obj.closing_date.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))
        obj.save()

    def save_formset(self, request, form, formset, change):
        if formset.model != Competitor:
            return super(CompetitionAdmin, self).save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
    
        if len(instances)>0:
            tz = instances[0].competition.timezone

        for instance in instances:
            if not instance.tracker_id:
                tracker = Tracker(publisher_id=request.user.pk)
                tracker.save()
                instance.tracker_id = tracker.pk

            if instance.starting_time is not None:
                instance.starting_time = utc.localize(tz.localize(instance.starting_time.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))

            instance.save()
	
        formset.save_m2m()


    class Media:
        js = {
            "//cdnjs.cloudflare.com/ajax/libs/moment.js/2.5.1/moment.min.js",
            "seuranta/js/jstz-1.0.5.min.js",
            "seuranta/admin/js/competition.js",
        }

admin.site.register(Tracker, TrackerAdmin)
admin.site.register(Competition, CompetitionAdmin)
