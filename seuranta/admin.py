import pytz
from .models import Competition, Competitor, RouteSection
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

class RouteSectionInlineAdmin(admin.TabularInline):
    model = RouteSection

class CompetitorInlineAdmin(admin.TabularInline):
    model = Competitor
    prepopulated_fields = {'shortname':('name',),}

class CompetitorAdmin(admin.ModelAdmin):
    inlines = [
        RouteSectionInlineAdmin,
    ]

    def queryset(self, request):
		qs = super(CompetitorAdmin, self).queryset(request)
		if request.user.is_superuser:
			return qs
		return qs.filter(competition__publisher=request.user)

    def has_add_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True

		if obj is None:
			return True
		else:
			return obj.competition.publisher == request.user

    def has_change_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True

		if obj is None:
			return True
		else:
			return obj.competition.publisher == request.user

    def has_delete_permission(self, request, obj=None):
		if request.user.is_superuser:
			return True

		if obj is None:
			return True
		else:
			return obj.competition.publisher == request.user


class CompetitionAdmin(PublisherAdmin):
    list_display = ('uuid', 'name', 'opening_date', 'closing_date', 'publication_policy')

    inlines = [
        CompetitorInlineAdmin,
    ]

#    def save_model(self, request, obj, form, change):
#        if obj.publisher_id is None:
#            obj.publisher = request.user
#        tz = obj.timezone
#        if obj.opening_date is not None:
#            obj.opening_date = utc.localize(tz.localize(obj.opening_date.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))
#
#        if obj.closing_date is not None:
#            obj.closing_date = utc.localize(tz.localize(obj.closing_date.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))
#        obj.save()

#    def save_formset(self, request, form, formset, change):
#        if formset.model != Competitor:
#            return super(CompetitionAdmin, self).save_formset(request, form, formset, change)
#        instances = formset.save(commit=False)
#
#        if len(instances)>0:
#            tz = instances[0].competition.timezone
#
#        for instance in instances:
#            if instance.starting_time is not None:
#                instance.starting_time = utc.localize(tz.localize(instance.starting_time.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))
#
#            instance.save()
#
#        formset.save_m2m()
#
#
    class Media:
        js = {
            "//cdnjs.cloudflare.com/ajax/libs/moment.js/2.5.1/moment.min.js",
            "seuranta/js/jstz-1.0.5.min.js",
            "seuranta/admin/js/competition.js",
        }

admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Competitor, CompetitorAdmin)
